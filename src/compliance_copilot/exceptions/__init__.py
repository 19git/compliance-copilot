"""Custom exceptions for Compliance Copilot.

All exceptions inherit from ComplianceCopilotError, making them easy to catch.
This hierarchy allows catching specific errors or whole categories.

Example:
    try:
        load_file("missing.csv")
    except FileNotFoundError as e:
        print(f"Specific file error: {e}")
    except ConnectorError as e:
        print(f"Any connector error: {e}")
    except ComplianceCopilotError as e:
        print(f"Any app error: {e}")
"""

# ─── BASE EXCEPTION ──────────────────────────────────────────

class ComplianceCopilotError(Exception):
    """Base exception for ALL Compliance Copilot errors.
    
    Every custom exception in this project inherits from this class.
    This lets users catch ANY error from our app with one except block.
    
    Example:
        >>> try:
        ...     run_compliance_check()
        ... except ComplianceCopilotError as e:
        ...     print(f"Compliance Copilot error: {e}")
    """
    
    def __init__(self, message: str, details: dict = None):
        """Create a new error with optional details.
        
        Args:
            message: Human-readable error description
            details: Extra structured information (file path, line number, etc.)
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        """Convert error to string, including details if present."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message
    
    def to_dict(self) -> dict:
        """Convert error to dictionary for logging/JSON output."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# ─── CONFIGURATION ERRORS ────────────────────────────────────

class ConfigurationError(ComplianceCopilotError):
    """Raised when there's a problem with configuration.
    
    Examples:
        - config.yaml file is missing
        - YAML syntax is invalid
        - Required setting is missing
        - Invalid value in config
    """
    pass


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when config file doesn't exist."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(
            f"Configuration file not found: {file_path}",
            {"file_path": file_path}
        )


class ConfigSyntaxError(ConfigurationError):
    """Raised when YAML syntax is invalid."""
    
    def __init__(self, file_path: str, line: int, error: str):
        self.file_path = file_path
        self.line = line
        self.error = error
        super().__init__(
            f"Invalid YAML in {file_path} at line {line}: {error}",
            {"file_path": file_path, "line": line, "error": error}
        )


class ConfigValidationError(ConfigurationError):
    """Raised when config values are invalid."""
    
    def __init__(self, field: str, value: any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            f"Invalid config value for '{field}': {value} - {reason}",
            {"field": field, "value": str(value), "reason": reason}
        )


# ─── CONNECTOR ERRORS ────────────────────────────────────────

class ConnectorError(ComplianceCopilotError):
    """Base class for ALL data connector errors.
    
    Connectors read data from files, APIs, databases.
    Any failure in that process uses these errors.
    """
    pass


class FileNotFoundError(ConnectorError):
    """Raised when a required file doesn't exist.
    
    Example:
        >>> raise FileNotFoundError("data.csv")
        FileNotFoundError: File not found: data.csv
    """
    
    def __init__(self, file_path: str, suggestion: str = None):
        """Create error with file path and optional suggestion.
        
        Args:
            file_path: Path to the missing file
            suggestion: How the user can fix this
        """
        self.file_path = file_path
        self.suggestion = suggestion
        
        message = f"File not found: {file_path}"
        details = {"file_path": file_path}
        
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
            details["suggestion"] = suggestion
        
        super().__init__(message, details)


class UnsupportedFormatError(ConnectorError):
    """Raised when trying to read an unsupported file format.
    
    Example:
        >>> supported = ['.csv', '.xlsx', '.pdf']
        >>> raise UnsupportedFormatError('.jpg', supported)
        UnsupportedFormatError: Unsupported format: .jpg
        Supported formats: .csv, .xlsx, .pdf
    """
    
    def __init__(self, format: str, supported_formats: list):
        """Create error with format info.
        
        Args:
            format: The format user tried (e.g., ".jpg")
            supported_formats: What we actually support
        """
        self.format = format
        self.supported_formats = supported_formats
        
        message = (
            f"Unsupported file format: {format}\n"
            f"Supported formats: {', '.join(supported_formats)}"
        )
        
        super().__init__(message, {
            "format": format,
            "supported_formats": supported_formats
        })


class DataLoadError(ConnectorError):
    """Raised when file exists but can't be loaded.
    
    Examples:
        - CSV file is empty
        - Excel file is corrupted
        - PDF has no extractable text
        - Wrong encoding
    """
    
    def __init__(self, file_path: str, reason: str, suggestion: str = None):
        """Create error with load failure reason.
        
        Args:
            file_path: Path to the problematic file
            reason: Why it couldn't be loaded
            suggestion: How to fix it
        """
        self.file_path = file_path
        self.reason = reason
        self.suggestion = suggestion
        
        message = f"Could not load {file_path}: {reason}"
        details = {"file_path": file_path, "reason": reason}
        
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
            details["suggestion"] = suggestion
        
        super().__init__(message, details)


class EmptyFileError(DataLoadError):
    """Raised when file has no data."""
    
    def __init__(self, file_path: str):
        super().__init__(file_path, "File is empty", "Check if the file contains data")


# ─── RULE ERRORS ─────────────────────────────────────────────

class RuleError(ComplianceCopilotError):
    """Base class for ALL rule-related errors.
    
    Rules are the heart of our system - these errors help
    users write correct rules.
    """
    pass


class RuleSyntaxError(RuleError):
    """Raised when a rule has invalid syntax.
    
    Example:
        User writes: "mfa_enabled = true"
        Should be:   "mfa_enabled == true"
    """
    
    def __init__(self, rule_id: str, line_number: int, error: str, 
                 suggestion: str = None, file_path: str = None):
        """Create error with rule location.
        
        Args:
            rule_id: ID of the rule (e.g., "MFA-001")
            line_number: Line in the file where error occurred
            error: What's wrong
            suggestion: How to fix it
            file_path: Which rule file
        """
        self.rule_id = rule_id
        self.line_number = line_number
        self.file_path = file_path
        
        # Build location string
        location = f"rule '{rule_id}'"
        if file_path:
            location = f"{file_path}:{line_number} ({rule_id})"
        
        message = f"Syntax error in {location}: {error}"
        details = {
            "rule_id": rule_id,
            "line_number": line_number,
            "error": error
        }
        
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
            details["suggestion"] = suggestion
        
        if file_path:
            details["file_path"] = file_path
        
        super().__init__(message, details)


class RuleValidationError(RuleError):
    """Raised when rule syntax is correct but values are invalid.
    
    Example:
        severity: "EXTREME"  # Should be LOW/MEDIUM/HIGH/CRITICAL
        condition: ""        # Empty condition not allowed
    """
    
    def __init__(self, rule_id: str, field: str, value: any, 
                 reason: str = None, valid_values: list = None):
        """Create validation error.
        
        Args:
            rule_id: Which rule has the problem
            field: Which field is invalid
            value: What value was provided
            reason: Why it's invalid
            valid_values: What values are allowed
        """
        self.rule_id = rule_id
        self.field = field
        self.value = value
        
        message = f"Rule '{rule_id}' has invalid {field}: '{value}'"
        details = {
            "rule_id": rule_id,
            "field": field,
            "value": str(value)
        }
        
        if reason:
            message += f" - {reason}"
            details["reason"] = reason
        
        if valid_values:
            message += f"\nValid values: {', '.join(str(v) for v in valid_values)}"
            details["valid_values"] = valid_values
        
        super().__init__(message, details)


class RuleExecutionError(RuleError):
    """Raised when a rule fails during execution.
    
    Examples:
        - Division by zero in condition
        - Referencing a column that doesn't exist
        - Type error (comparing string to number)
    """
    
    def __init__(self, rule_id: str, condition: str, error: str, 
                 row_data: dict = None):
        """Create execution error.
        
        Args:
            rule_id: Which rule failed
            condition: The condition that failed
            error: What went wrong
            row_data: The data row that caused the failure
        """
        self.rule_id = rule_id
        self.condition = condition
        
        message = f"Rule '{rule_id}' failed during execution: {error}\n"
        message += f"Condition: {condition}"
        
        details = {
            "rule_id": rule_id,
            "condition": condition,
            "error": error
        }
        
        if row_data:
            # Include first few rows for debugging (but don't blow up)
            sample = dict(list(row_data.items())[:5])
            details["sample_row"] = sample
            message += f"\nSample row: {sample}"
        
        super().__init__(message, details)


# ─── SECURITY ERRORS ─────────────────────────────────────────

class SecurityError(ComplianceCopilotError):
    """Base class for ALL security-related errors.
    
    These errors indicate potential security issues.
    """
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails.
    
    Example: Invalid API key, expired token
    """
    
    def __init__(self, reason: str = "Invalid credentials", 
                 suggestion: str = None):
        """Create authentication error."""
        message = f"Authentication failed: {reason}"
        details = {"reason": reason}
        
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
            details["suggestion"] = suggestion
        
        super().__init__(message, details)


class AuthorizationError(SecurityError):
    """Raised when user lacks permission.
    
    Example: User tries to run admin-only rules
    """
    
    def __init__(self, resource: str, required_role: str = None, 
                 user_role: str = None):
        """Create authorization error.
        
        Args:
            resource: What they tried to access
            required_role: What role they need
            user_role: What role they have
        """
        message = f"Not authorized to access: {resource}"
        details = {"resource": resource}
        
        if required_role:
            message += f" (requires role: {required_role})"
            details["required_role"] = required_role
        
        if user_role:
            message += f" (your role: {user_role})"
            details["user_role"] = user_role
        
        super().__init__(message, details)


# ─── INTERNAL ERRORS ─────────────────────────────────────────

class InternalError(ComplianceCopilotError):
    """Raised for unexpected internal errors.
    
    These should never happen - if they do, it's a bug in our code.
    """
    
    def __init__(self, message: str, component: str = None, 
                 bug_report: bool = True):
        """Create internal error.
        
        Args:
            message: What went wrong
            component: Which part of the system failed
            bug_report: Whether to suggest reporting the bug
        """
        details = {}
        if component:
            details["component"] = component
        
        full_message = f"Internal error: {message}"
        if bug_report:
            full_message += "\nThis is a bug. Please report it!"
            details["bug_report"] = True
        
        super().__init__(full_message, details)


# ─── LIST OF ALL EXPORTED EXCEPTIONS ─────────────────────────

__all__ = [
    # Base
    'ComplianceCopilotError',
    
    # Configuration
    'ConfigurationError',
    'ConfigFileNotFoundError',
    'ConfigSyntaxError',
    'ConfigValidationError',
    
    # Connector
    'ConnectorError',
    'FileNotFoundError',
    'UnsupportedFormatError',
    'DataLoadError',
    'EmptyFileError',
    
    # Rule
    'RuleError',
    'RuleSyntaxError',
    'RuleValidationError',
    'RuleExecutionError',
    
    # Security
    'SecurityError',
    'AuthenticationError',
    'AuthorizationError',
    
    # Internal
    'InternalError',
]
