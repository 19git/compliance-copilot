"""Main rule engine that orchestrates everything."""

import time
from typing import List, Optional
from pathlib import Path
import pandas as pd

from ..connectors.factory import ConnectorFactory
from .models import Rule, RuleResult, RuleStatus
from .rule_parser import RuleParser
from .expression_evaluator import ExpressionEvaluator


class RuleEngine:
    """Main engine for evaluating compliance rules."""
    
    def __init__(self, config: dict = None, debug: bool = False):
        self.config = config or {}
        self.debug = debug
        self.parser = RuleParser()
        self.evaluator = ExpressionEvaluator(debug=debug)
        self.factory = ConnectorFactory(self.config.get('connectors', {}))
        
        self.stats = {
            "rules_loaded": 0,
            "rules_executed": 0,
            "total_rows_processed": 0
        }
    
    def run(self, rule_source: str, data_path: str) -> List[RuleResult]:
        """Run compliance checks."""
        start_time = time.time()
        
        # Load rules
        rules = self._load_rules(rule_source)
        self.stats["rules_loaded"] = len(rules)
        
        if self.debug:
            print(f"Loaded {len(rules)} rules")
        
        # Group rules by data source
        rules_by_source = {}
        for rule in rules:
            if rule.data_source not in rules_by_source:
                rules_by_source[rule.data_source] = []
            rules_by_source[rule.data_source].append(rule)
        
        # Execute rules
        all_results = []
        
        for source, source_rules in rules_by_source.items():
            # Resolve full path
            full_path = str(Path(data_path) / source)
            
            if self.debug:
                print(f"\nLoading data from: {full_path}")
            
            try:
                # Load data once for all rules using same source
                data = self._load_data(full_path)
                
                # Apply each rule
                for rule in source_rules:
                    result = self._evaluate_rule(rule, data)
                    all_results.append(result)
                    
            except Exception as e:
                if self.debug:
                    print(f"Error loading {full_path}: {e}")
                
                for rule in source_rules:
                    result = RuleResult(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        status=RuleStatus.ERROR,
                        error_message=str(e)
                    )
                    all_results.append(result)
        
        self.stats["total_execution_time"] = (time.time() - start_time) * 1000
        return all_results
    
    def _load_rules(self, rule_source: str) -> List[Rule]:
        """Load rules from file or directory."""
        path = Path(rule_source)
        
        if path.is_file():
            return self.parser.parse_file(str(path))
        elif path.is_dir():
            rules = []
            for rule_file in path.glob("*.yaml"):
                rules.extend(self.parser.parse_file(str(rule_file)))
            return rules
        else:
            raise FileNotFoundError(f"Rule source not found: {rule_source}")
    
    def _load_data(self, source: str) -> pd.DataFrame:
        """Load data using appropriate connector."""
        connector = self.factory.get_connector(source)
        return connector.load(source)
    
    def _evaluate_rule(self, rule: Rule, data: pd.DataFrame) -> RuleResult:
        """Evaluate a single rule against data."""
        rule_start = time.time()
        
        result = RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            status=RuleStatus.PASS,
            total_rows=len(data)
        )
        
        try:
            # Apply filter if specified
            if rule.filter:
                filtered_data = data.query(rule.filter)
            else:
                filtered_data = data
            
            result.total_rows = len(filtered_data)
            
            # Evaluate each row
            violations = []
            passed = 0
            
            for idx, row in filtered_data.iterrows():
                passes = self.evaluator.evaluate(rule.condition, row.to_dict())
                
                if passes:
                    passed += 1
                else:
                    violations.append({
                        "row_index": idx,
                        "row_data": row.to_dict()
                    })
            
            result.passed_rows = passed
            result.failed_rows = len(violations)
            result.violations = violations
            
            if result.failed_rows > 0:
                result.status = RuleStatus.FAIL
            
            self.stats["total_rows_processed"] += result.total_rows
            
        except Exception as e:
            result.status = RuleStatus.ERROR
            result.error_message = str(e)
        
        result.execution_time_ms = (time.time() - rule_start) * 1000
        self.stats["rules_executed"] += 1
        
        return result
    
    def get_stats(self):
        """Get engine statistics."""
        return self.stats
