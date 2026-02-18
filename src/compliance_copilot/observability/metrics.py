"""Simple metrics collection for Compliance Copilot."""

import time
from typing import Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import json


class MetricsCollector:
    """Collect and report metrics."""
    
    def __init__(self, metrics_dir: str = "metrics"):
        """Initialize metrics collector."""
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.counters = Counter()
        self.gauges = {}
        self.timers = []
        self.session_start = datetime.utcnow()
        self.last_snapshot = datetime.utcnow()
    
    def increment(self, name: str, value: int = 1, tags: Optional[Dict] = None):
        """Increment a counter."""
        key = self._format_key(name, tags)
        self.counters[key] += value
    
    def gauge(self, name: str, value: float, tags: Optional[Dict] = None):
        """Set a gauge value."""
        key = self._format_key(name, tags)
        self.gauges[key] = value
    
    def timer(self, name: str, tags: Optional[Dict] = None):
        """Context manager for timing operations."""
        return _TimerContext(self, name, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict] = None):
        """Record a timer value manually."""
        key = self._format_key(name, tags)
        self.timers.append({
            "name": key,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _format_key(self, name: str, tags: Optional[Dict] = None) -> str:
        """Format metric key with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.session_start).total_seconds(),
            "counters": dict(self.counters),
            "gauges": self.gauges,
            "timers": self._summarize_timers()
        }
    
    def _summarize_timers(self) -> Dict[str, Any]:
        """Calculate statistics for timers."""
        if not self.timers:
            return {}
        
        # Group by name
        by_name = {}
        for timer in self.timers:
            name = timer["name"]
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(timer["duration_ms"])
        
        # Calculate stats
        summary = {}
        for name, values in by_name.items():
            summary[name] = {
                "count": len(values),
                "min_ms": min(values),
                "max_ms": max(values),
                "avg_ms": sum(values) / len(values),
                "total_ms": sum(values),
                "p95_ms": sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else None
            }
        
        return summary
    
    def save_snapshot(self, filename: Optional[str] = None) -> Path:
        """Save current metrics to a JSON file."""
        if filename is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"metrics_{timestamp}.json"
        
        filepath = self.metrics_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.summary(), f, indent=2)
        
        self.last_snapshot = datetime.utcnow()
        return filepath


class _TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict] = None):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = (time.perf_counter() - self.start_time) * 1000
            self.collector.record_timer(self.name, duration, self.tags)
