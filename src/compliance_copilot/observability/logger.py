"""Structured logging for Compliance Copilot."""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler


class StructuredLogger:
    """Logger that outputs structured JSON logs."""
    
    def __init__(self, 
                 name: str,
                 log_dir: str = "logs",
                 level: str = "INFO",
                 console: bool = True,
                 json_file: bool = True):
        """Initialize the structured logger."""
        self.name = name
        self.log_dir = Path(log_dir)
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.console_enabled = console
        
        # Create log directory
        if json_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.utcnow().strftime('%Y%m%d')
            log_file = self.log_dir / f"{name}_{date_str}.jsonl"
            self.file_handler = RotatingFileHandler(
                log_file, maxBytes=10_485_760, backupCount=5
            )
        else:
            self.file_handler = None
    
    def debug(self, event: str, **kwargs):
        """Log a debug event."""
        self._log(logging.DEBUG, event, kwargs)
    
    def info(self, event: str, **kwargs):
        """Log an info event."""
        self._log(logging.INFO, event, kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log a warning event."""
        self._log(logging.WARNING, event, kwargs)
    
    def error(self, event: str, **kwargs):
        """Log an error event."""
        self._log(logging.ERROR, event, kwargs)
    
    def _log(self, level: int, event: str, data: Dict[str, Any]):
        """Internal method that does the actual logging."""
        if level < self.level:
            return
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": self.name,
            "level": logging.getLevelName(level),
            "event": event,
            **data
        }
        
        if self.console_enabled:
            self._write_console(log_entry)
        
        if self.file_handler:
            self._write_json_file(log_entry)
    
    def _write_console(self, entry: Dict[str, Any]):
        """Write human-readable log to console."""
        level = entry["level"]
        event = entry["event"]
        timestamp = entry["timestamp"][11:19]
        
        # Color coding for different levels
        if level == "ERROR":
            prefix = "🔴"
        elif level == "WARNING":
            prefix = "🟡"
        elif level == "INFO":
            prefix = "🔵"
        else:
            prefix = "⚪"
        
        console_msg = f"{prefix} [{level:8}] {timestamp} - {event}"
        
        skip_fields = {"timestamp", "logger", "level", "event"}
        for key, value in entry.items():
            if key not in skip_fields:
                console_msg += f" - {key}={value}"
        
        print(console_msg)
    
    def _write_json_file(self, entry: Dict[str, Any]):
        """Write JSON log to file."""
        try:
            self.file_handler.stream.write(json.dumps(entry) + "\n")
            self.file_handler.flush()
        except Exception:
            print(f"Failed to write log: {entry}", file=sys.stderr)
