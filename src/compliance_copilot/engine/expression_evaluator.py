"""Safely evaluate rule conditions."""

import operator
from typing import Dict, Any
import pandas as pd


class ExpressionEvaluator:
    """Safely evaluates rule conditions against data rows."""
    
    # Allowed operators
    _operators = {
        '==': operator.eq,
        '!=': operator.ne,
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        'and': lambda a, b: a and b,
        'or': lambda a, b: a or b,
        'not': operator.not_,
        'in': lambda a, b: a in b,
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
    }
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def evaluate(self, condition: str, row: Dict[str, Any]) -> bool:
        """Evaluate condition against a single row."""
        if self.debug:
            print(f"  Evaluating: {condition}")
            print(f"  Row data: {row}")
        
        try:
            # Create safe evaluation context
            context = self._create_context(row)
            result = eval(condition, {"__builtins__": {}}, context)
            
            if self.debug:
                print(f"  Result: {result}")
            
            return bool(result)
            
        except Exception as e:
            if self.debug:
                print(f"  Error: {e}")
            return False
    
    def _create_context(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Create evaluation context from row data."""
        # Convert pandas Series to dict if needed
        if isinstance(row, pd.Series):
            row = row.to_dict()
        
        # Start with built-in constants
        context = {
            'True': True,
            'False': False,
            'None': None,
        }
        
        # Add row data
        context.update(row)
        
        # Add allowed operators
        context.update(self._operators)
        
        return context
