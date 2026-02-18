"""Observability module - see what's happening inside.

Provides:
- Structured logging
- Metrics collection
- Distributed tracing
- Error tracking
"""

from .logger import StructuredLogger
from .metrics import MetricsCollector
from .tracing import Tracer
from .errors import ErrorTracker, ErrorCategory

__all__ = [
    'StructuredLogger',
    'MetricsCollector',
    'Tracer',
    'ErrorTracker',
    'ErrorCategory',
]
