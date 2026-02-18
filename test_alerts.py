#!/usr/bin/env python3
"""Test script for alerts."""

from src.compliance_copilot.notifier import Notifier
from src.compliance_copilot.engine.models import RuleResult, RuleStatus
from datetime import datetime

# Create sample failures
failures = []
for i in range(3):
    result = RuleResult(
        rule_id=f"TEST-00{i+1}",
        rule_name=f"Test Rule {i+1}",
        status=RuleStatus.FAIL,
        total_rows=100,
        passed_rows=75,
        failed_rows=25,
        violations=[
            {
                "row_index": 5,
                "row_data": {
                    "username": f"user{i}@example.com",
                    "department": "Engineering",
                    "mfa_enabled": False
                }
            },
            {
                "row_index": 12,
                "row_data": {
                    "username": f"user{i+1}@example.com", 
                    "department": "Sales",
                    "mfa_enabled": False
                }
            }
        ]
    )
    failures.append(result)

summary = {
    'total': 10,
    'passed': 5,
    'failed': 3,
    'errors': 2
}

# Test with config file
import yaml
with open('config.with-alerts.yaml', 'r') as f:
    config = yaml.safe_load(f)

notifier = Notifier(config.get('alerts', {}))
print("Sending test alerts...")
notifier.send_alerts(failures, "TEST_SCAN_001", summary)
print("Done!")
