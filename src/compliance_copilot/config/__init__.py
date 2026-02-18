"""Configuration management for Compliance Copilot.

This module handles loading, validating, and accessing configuration
from multiple sources: defaults, config files, and environment variables.
"""

from .loader import ConfigLoader
from .schema import ComplianceConfig

__all__ = ['ConfigLoader', 'ComplianceConfig']
