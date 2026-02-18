"""Compliance Copilot - A modular compliance rule engine.

This package helps you check if your data follows your rules.
It reads data from files, applies YAML-defined rules, and reports violations.
"""

__version__ = "0.1.0-alpha"

from .config import ConfigLoader, ComplianceConfig
from .connectors import ConnectorFactory
from .exceptions import *
from .utils import *

__all__ = [
    'ConfigLoader',
    'ComplianceConfig',
    'ConnectorFactory',
]
