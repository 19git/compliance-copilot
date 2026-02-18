"""Parse YAML rule files into Rule objects."""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from .models import Rule, Severity


class RuleParser:
    """Parses YAML rule definitions into Rule objects."""
    
    def __init__(self):
        self.defaults = {
            "severity": "MEDIUM",
            "enabled": True
        }
    
    def parse_file(self, file_path: str) -> List[Rule]:
        """Parse YAML file into list of Rules."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Rule file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return []
        
        # Handle both single rule and list of rules
        if isinstance(data, dict) and 'rules' in data:
            rules_data = data['rules']
        elif isinstance(data, list):
            rules_data = data
        else:
            rules_data = [data]
        
        return [self._create_rule(rule_dict) for rule_dict in rules_data]
    
    def _create_rule(self, rule_dict: Dict[str, Any]) -> Rule:
        """Create Rule object from dictionary."""
        # Apply defaults
        for key, value in self.defaults.items():
            if key not in rule_dict:
                rule_dict[key] = value
        
        # Convert string severity to Enum
        if 'severity' in rule_dict and isinstance(rule_dict['severity'], str):
            rule_dict['severity'] = Severity[rule_dict['severity'].upper()]
        
        return Rule(**rule_dict)
