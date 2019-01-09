"""
All Rules that are related to comparison operators:
==, !=, <, >, <=, >=
They behave the same as you might expect from Python comparison operators.
"""

import logging
from abc import ABCMeta

from ..rules.base import Rule


log = logging.getLogger(__name__)


class OperatorRule(Rule, metaclass=ABCMeta):
    """
    Base class for all Logic Operator Rules
    """
    def __init__(self, val):
        self.val = val


class Eq(OperatorRule):
    """Rule that is satisfied when two values are equal '=='"""
    def satisfied(self, what, inquiry=None):
        if isinstance(self.val, tuple):
            val = list(self.val)
        else:
            val = self.val
        return val == what


class NotEq(OperatorRule):
    """Rule that is satisfied when two values are not equal '!='"""
    def satisfied(self, what, inquiry=None):
        if isinstance(self.val, tuple):
            val = list(self.val)
        else:
            val = self.val
        return val != what


class Greater(OperatorRule):
    """Rule that is satisfied when 'what' is greater '>' than initial value"""
    def satisfied(self, what, inquiry=None):
        return what > self.val


class Less(OperatorRule):
    """Rule that is satisfied when 'what' is less '<' than initial value"""
    def satisfied(self, what, inquiry=None):
        return what < self.val


class GreaterOrEqual(OperatorRule):
    """Rule that is satisfied when 'what' is greater or equal '>=' than initial value"""
    def satisfied(self, what, inquiry=None):
        return what >= self.val


class LessOrEqual(OperatorRule):
    """Rule that is satisfied when 'what' is less or equal '<=' than initial value"""
    def satisfied(self, what, inquiry=None):
        return what <= self.val
