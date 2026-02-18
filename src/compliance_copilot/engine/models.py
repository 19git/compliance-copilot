"""Data models for rules and results."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class Severity(Enum):
    """Rule severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleStatus(Enum):
    """Result status for a rule evaluation."""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class Rule:
    """A single compliance rule."""
    
    # Required fields
    id: str
    name: str
    condition: str
    data_source: str
    
    # Optional fields
    description: str = ""
    severity: Severity = Severity.MEDIUM
    filter: Optional[str] = None
    enabled: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def validate(self) -> List[str]:
        """Validate rule definition."""
        errors = []
        if not self.id:
            errors.append("Rule ID cannot be empty")
        if not self.name:
            errors.append("Rule name cannot be empty")
        if not self.condition:
            errors.append("Rule condition cannot be empty")
        if not self.data_source:
            errors.append("Data source cannot be empty")
        return errors


@dataclass
class RuleResult:
    """Result of evaluating a rule."""
    
    rule_id: str
    rule_name: str
    status: RuleStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Counts
    total_rows: int = 0
    passed_rows: int = 0
    failed_rows: int = 0
    
    # Details
    violations: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    
    # Performance
    execution_time_ms: float = 0.0
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.passed_rows / self.total_rows) * 100
    
    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Rule: {self.rule_id} - {self.rule_name}\n"
            f"Status: {self.status.value}\n"
            f"Pass Rate: {self.pass_rate:.1f}% ({self.passed_rows}/{self.total_rows})\n"
            f"Violations: {self.failed_rows}"
        )
