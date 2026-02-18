"""Simple request tracing for Compliance Copilot."""

import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Span:
    """A single operation within a trace."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    parent_id: Optional[str] = None


class Tracer:
    """Simple tracer for distributed tracing."""
    
    def __init__(self, service_name: str = "compliance-copilot"):
        self.service_name = service_name
        self.current_trace = None
        self.spans = []
    
    @contextmanager
    def trace(self, name: str, attributes: Optional[Dict] = None):
        """Create a new trace."""
        trace_id = str(uuid.uuid4())[:8]
        
        root_span = Span(
            name=name,
            start_time=time.time(),
            attributes=attributes or {}
        )
        
        old_trace = self.current_trace
        self.current_trace = {
            "trace_id": trace_id,
            "root_span": root_span,
            "current_span": root_span,
            "start_time": datetime.utcnow()
        }
        self.spans = [root_span]
        
        try:
            yield _TraceContext(self)
        finally:
            root_span.end_time = time.time()
            self._log_trace()
            self.current_trace = old_trace
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict] = None):
        """Create a child span within current trace."""
        if not self.current_trace:
            yield
            return
        
        parent = self.current_trace["current_span"]
        span = Span(
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
            parent_id=id(parent)
        )
        
        old_span = self.current_trace["current_span"]
        self.current_trace["current_span"] = span
        self.spans.append(span)
        
        try:
            yield _SpanContext(self, span)
        finally:
            span.end_time = time.time()
            self.current_trace["current_span"] = old_span
    
    def add_event(self, name: str, **attributes):
        """Add an event to current span."""
        if not self.current_trace:
            return
        span = self.current_trace["current_span"]
        span.events.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "attributes": attributes
        })
    
    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span."""
        if not self.current_trace:
            return
        span = self.current_trace["current_span"]
        span.attributes[key] = value
    
    def _log_trace(self):
        """Log the completed trace."""
        if not self.current_trace:
            return
        
        trace = self.current_trace
        root = trace["root_span"]
        duration = (root.end_time - root.start_time) * 1000
        
        print(f"\n🔍 Trace: {root.name} ({trace['trace_id']})")
        print(f"   Duration: {duration:.2f}ms")
        print(f"   Spans: {len(self.spans)}")
        
        # Print span tree
        for i, span in enumerate(self.spans):
            indent = "  " * (1 if span.parent_id else 0)
            span_duration = (span.end_time - span.start_time) * 1000
            attrs = f" {span.attributes}" if span.attributes else ""
            print(f"{indent}• {span.name} ({span_duration:.2f}ms){attrs}")
            
            for event in span.events:
                print(f"{indent}  ⚡ {event['name']}")


class _TraceContext:
    def __init__(self, tracer: Tracer):
        self.tracer = tracer
    
    def span(self, name: str, attributes: Optional[Dict] = None):
        return self.tracer.span(name, attributes)
    
    def add_event(self, name: str, **attributes):
        self.tracer.add_event(name, **attributes)
    
    def set_attribute(self, key: str, value: Any):
        self.tracer.set_attribute(key, value)


class _SpanContext:
    def __init__(self, tracer: Tracer, span: Span):
        self.tracer = tracer
        self.span = span
    
    def add_event(self, name: str, **attributes):
        self.tracer.add_event(name, **attributes)
    
    def set_attribute(self, key: str, value: Any):
        self.tracer.set_attribute(key, value)
