"""Error tracking and categorization."""

import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json


class ErrorCategory:
    """Error categories for classification."""
    
    CONFIGURATION = "configuration"
    CONFIG_SYNTAX = "config_syntax"
    CONFIG_VALIDATION = "config_validation"
    CONNECTOR = "connector"
    FILE_NOT_FOUND = "file_not_found"
    UNSUPPORTED_FORMAT = "unsupported_format"
    DATA_LOAD = "data_load"
    RULE = "rule"
    RULE_SYNTAX = "rule_syntax"
    RULE_VALIDATION = "rule_validation"
    RULE_EXECUTION = "rule_execution"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SYSTEM = "system"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorTracker:
    """Track and categorize errors."""
    
    def __init__(self, error_dir: str = "errors"):
        self.error_dir = Path(error_dir)
        self.error_dir.mkdir(parents=True, exist_ok=True)
        self.errors = []
    
    def track(self,
              error: Exception,
              category: str = ErrorCategory.UNKNOWN,
              context: Optional[Dict] = None,
              user_message: Optional[str] = None,
              severity: str = "ERROR"):
        """Track an error."""
        stack_trace = traceback.format_exc()
        
        if user_message is None:
            user_message = self._generate_user_message(error, category)
        
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": category,
            "severity": severity,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "user_message": user_message,
            "stack_trace": stack_trace,
            "context": context or {}
        }
        
        self.errors.append(error_entry)
        self._save_error(error_entry)
        
        # Also print to console with nice formatting
        icon = "🔴" if severity == "ERROR" else "🟡" if severity == "WARNING" else "⚪"
        print(f"{icon} Error: {user_message}")
    
    def _generate_user_message(self, error: Exception, category: str) -> str:
        """Generate user-friendly error message."""
        messages = {
            ErrorCategory.CONFIGURATION: "Configuration error. Check your YAML files.",
            ErrorCategory.CONFIG_SYNTAX: "Invalid YAML syntax in configuration.",
            ErrorCategory.FILE_NOT_FOUND: f"File not found: {error}",
            ErrorCategory.UNSUPPORTED_FORMAT: "Unsupported file format. Use CSV, Excel, or PDF.",
            ErrorCategory.DATA_LOAD: f"Could not load data: {error}",
            ErrorCategory.RULE_SYNTAX: "Rule syntax error. Check your conditions.",
            ErrorCategory.RULE_VALIDATION: "Rule validation failed.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Check your API key.",
        }
        return messages.get(category, f"Error: {error}")
    
    def _save_error(self, error_entry: Dict):
        """Save error to file."""
        date_str = datetime.utcnow().strftime('%Y%m%d')
        error_file = self.error_dir / f"errors_{date_str}.jsonl"
        
        with open(error_file, 'a') as f:
            f.write(json.dumps(error_entry) + "\n")
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent errors."""
        return self.errors[-limit:]
    
    def summary(self) -> Dict[str, int]:
        """Get error summary by category."""
        summary = {}
        for error in self.errors:
            cat = error["category"]
            summary[cat] = summary.get(cat, 0) + 1
        return summary
    
    def clear(self):
        """Clear in-memory errors."""
        self.errors = []
