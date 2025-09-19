"""
An API wrapper for PRONOTE
"""
# ruff: noqa: F401

__title__ = "pronotepy"
__author__ = "bain, Xiloe"
__license__ = "MIT"
__copyright__ = "Copyright (c) bain, Xiloe"
__version__ = "3.0.0"

from .err import *
from .session import *
from .clients import *
from .simple_objects import *
from .credentials import *

from .term import *

from .parse import GradeValue, SpecialGradeValue
