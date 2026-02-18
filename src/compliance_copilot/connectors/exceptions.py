"""Connector-specific exceptions.

WHY CUSTOM EXCEPTIONS?
-----------------------
Python has built-in exceptions, but they're too generic.
We want to catch SPECIFIC errors:
- File not found? Handle it differently from "wrong format"
- Empty file? Tell user it's empty, not just "error"

This makes error messages HELPFUL instead of confusing.
"""

class ConnectorError(Exception):
    """BASE class for all connector errors.
    
    All other connector exceptions inherit from this.
    This lets you catch ANY connector error with:
    
        try:
            df = connector.load("file.csv")
        except ConnectorError as e:
            print(f"Connector error: {e}")
    """
    pass


class FileNotFoundError(ConnectorError):
    """Raised when a file DOESN'T EXIST.
    
    Example:
        >>> raise FileNotFoundError("missing.csv")
        FileNotFoundError: File not found: missing.csv
    """
    
    def __init__(self, file_path: str, message: str = None):
        """Create error with file path.
        
        Args:
            file_path: Path to the missing file
            message: Custom message (auto-generated if None)
        """
        self.file_path = file_path
        if message is None:
            message = f"File not found: {file_path}"
        super().__init__(message)


class UnsupportedFormatError(ConnectorError):
    """Raised when file FORMAT isn't supported.
    
    Example:
        >>> supported = ['.csv', '.xlsx', '.pdf']
        >>> raise UnsupportedFormatError('.jpg', supported)
        UnsupportedFormatError: Unsupported format: .jpg. Supported: .csv, .xlsx, .pdf
    """
    
    def __init__(self, format: str, supported_formats: list):
        """Create error with format info.
        
        Args:
            format: The format user tried (e.g., '.jpg')
            supported_formats: What we actually support
        """
        self.format = format
        self.supported_formats = supported_formats
        message = (
            f"Unsupported format: {format}\n"
            f"Supported formats: {', '.join(supported_formats)}"
        )
        super().__init__(message)


class DataLoadError(ConnectorError):
    """Raised when file EXISTS but CAN'T BE LOADED.
    
    Examples:
        - CSV file is corrupted
        - Excel file is password protected
        - PDF has no extractable text
        
    This is different from FileNotFoundError - the file is there,
    but something went wrong reading it.
    """
    
    def __init__(self, file_path: str, reason: str):
        """Create error with failure reason.
        
        Args:
            file_path: Path to the problematic file
            reason: Why it couldn't be loaded
        """
        self.file_path = file_path
        self.reason = reason
        message = f"Could not load {file_path}: {reason}"
        super().__init__(message)


class EmptyFileError(DataLoadError):
    """SPECIFIC case of DataLoadError - file has NO DATA.
    
    Example:
        >>> raise EmptyFileError("empty.csv")
        EmptyFileError: Could not load empty.csv: File is empty
    """
    
    def __init__(self, file_path: str):
        """Create error for empty file."""
        super().__init__(file_path, "File is empty")
