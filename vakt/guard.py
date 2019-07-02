""""
Main module that serves as an entry point for Vakt decisions.
Also contains Inquiry class.
"""

import logging

from .cache import AllowanceCache
from .util import JsonSerializer, PrettyPrint


log = logging.getLogger(__name__)


class Inquiry(JsonSerializer, PrettyPrint):
    """Holds all the information about the inquired intent.
    Is responsible to decisions if the inquired intent allowed or not."""

    def __init__(self, resource=None, action=None, subject=None, context=None):
        # explicitly assign empty strings instead of occasional None, (), etc.
        self.resource = resource or ''
        self.action = action or ''
        self.subject = subject or ''
        self.context = context or {}

    @classmethod
    def from_json(cls, data):
        props = cls._parse(data)
        return cls(**props)

    def to_json_sorted(self):
        """
        Get JSON representation with all keys sorted.
        """
        return super().to_json(sort=True)

    def __eq__(self, other):
        """
        If inquiries have the same contents - they are equal
        """
        return self.to_json_sorted() == other.to_json_sorted()

    def __hash__(self):
        """
        We do not use to_json as contents representation, because strings are not guaranteed
        to be hashed consistently across different python processes.
        """
        return hash(tuple((ord(c) for c in self.to_json_sorted())))


class Guard:
    """
    Executor of policy checks.
    Given a storage and a checker it can decide via `is_allowed` method if a given inquiry allowed or not.
    """

    def __init__(self, storage, checker):
        self.storage = storage
        self.checker = checker

    def is_allowed(self, inquiry):
        """
        Is given inquiry intent allowed or not?
        Same as `is_allowed_silent`, but also logs answers.
        Is meant to be used by an end-user.
        """
        answer = self.is_allowed_silent(inquiry)
        if answer:
            log.info('Incoming Inquiry was allowed. Inquiry: %s', inquiry)
        else:
            log.info('Incoming Inquiry was rejected. Inquiry: %s', inquiry)
        return answer

    def is_allowed_silent(self, inquiry):
        """
        Is given inquiry intent allowed or not?
        Does not log answers.
        Is not meant to be called by an end-user. Use it only if you want the core functionality of allowance check.
        """
        try:
            policies = self.storage.find_for_inquiry(inquiry, self.checker)
            # Storage is not obliged to do the exact policies match. It's up to the storage
            # to decide what policies to return. So we need a more correct programmatically done check.
            answer = self.check_policies_allow(inquiry, policies)
        except Exception:
            log.exception('Unexpected exception occurred while checking Inquiry %s', inquiry)
            answer = False
        return answer

    def check_policies_allow(self, inquiry, policies):
        """
        Check if any of a given policy allows a specified inquiry
        """
        # If no policies found or None is given -> deny access!
        if not policies:
            return False

        # Filter policies that fit Inquiry by its attributes.
        filtered = [p for p in policies if
                    self.checker.fits(p, 'actions', inquiry.action) and
                    self.checker.fits(p, 'subjects', inquiry.subject) and
                    self.checker.fits(p, 'resources', inquiry.resource) and
                    self.check_context_restriction(p, inquiry)]

        # no policies -> deny access!
        # if we have 2 or more similar policies - all of them should have allow effect, otherwise -> deny access!
        return len(filtered) > 0 and all(p.allow_access() for p in filtered)

    @staticmethod
    def check_context_restriction(policy, inquiry):
        """
        Check if context restriction in the policy is satisfied for a given inquiry's context.
        If at least one rule is not present in Inquiry's context -> deny access.
        If at least one rule provided in Inquiry's context is not satisfied -> deny access.
        """
        for key, rule in policy.context.items():
            try:
                ctx_value = inquiry.context[key]
            except KeyError:
                log.debug("No key '%s' found in Inquiry context", key)
                return False
            if not rule.satisfied(ctx_value, inquiry):
                return False
        return True


class CachedGuard(Guard):
    """
    Guard whose `is_allowed` calls are cached.
    If helps to increase performance for similar Inquiries in case you have static Policies set.

    cache - argument allows you to provide your own cache implementation that must
    implement vakt.cache.AllowanceCacheBackend. If it is None the default in-memory LRU cache will be used.
    It also accepts optional keyword arguments that will be passed to a cache. Currently only `maxsize` is available.
    maxsize - argument allows you to specify a maximum size of a default in-memory LRU cache, (preferably a power of 2)
    """
    def __init__(self, storage, checker, cache=None, **kwargs):
        super().__init__(storage, checker)
        self._cache = AllowanceCache(self, cache_backend=cache, **kwargs)

    @property
    def cache(self):
        """
        Get AllowanceCache of this guard.
        """
        return self._cache
