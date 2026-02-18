"""Base classes for all data connectors.

WHY DO WE NEED THIS?
--------------------
All connectors (CSV, Excel, PDF, etc.) should work the SAME way.
If we have a base class, we can guarantee that every connector has:
- a load() method (to read data)
- a validate() method (to check if file exists)
- get_metadata() method (to know what was loaded)

This is called "polymorphism" - same interface, different implementations.
"""

from abc import ABC, abstractmethod  # ABC = Abstract Base Class
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime

# We'll import our exceptions later when we create them
# from ..exceptions import FileNotFoundError, DataLoadError


class BaseConnector(ABC):
    """ABSTRACT base class for all data connectors.
    
    "Abstract" means you CANNOT use this class directly.
    You MUST create a child class (like CSVConnector) that implements
    the abstract methods.
    
    Think of this as a CONTRACT: any class that inherits from BaseConnector
    MUST implement load() and validate().
    
    Example of what you CANNOT do:
        >>> connector = BaseConnector()  # ERROR! Abstract class
    
    Example of what you CAN do:
        >>> class CSVConnector(BaseConnector):
        ...     def load(self, source):
        ...         # actual CSV reading code here
        ...         pass
        ...     def validate(self, source):
        ...         # actual validation code here
        ...         pass
        >>> connector = CSVConnector()  # OK! Child class
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize connector with optional configuration.
        
        Args:
            config: Connector-specific configuration (from config.yaml)
                   Example: {"delimiter": ",", "encoding": "utf-8"}
        
        Why have config?
        -----------------
        Different files need different settings:
        - CSV files might use commas or tabs
        - Excel files might need a specific sheet
        - PDFs might need a password
        
        The config dictionary lets users customize without changing code.
        """
        # If no config provided, use empty dict
        self.config = config or {}
        
        # _metadata (with underscore) is "private" - don't access directly
        # Use get_metadata() instead
        self._metadata = {}
        
        print(f"✅ Initialized {self.__class__.__name__}")  # Debug output
    
    @abstractmethod
    def load(self, source: str, **kwargs) -> pd.DataFrame:
        """LOAD data from source into pandas DataFrame.
        
        This is the MOST IMPORTANT method. Every connector MUST implement it.
        
        Args:
            source: Path to file or other source identifier
                   Examples: "data/users.csv", "/home/user/data.xlsx"
            **kwargs: Connector-specific options that override config
                     Example: load("data.csv", delimiter="\t")  # use tab
            
        Returns:
            pandas DataFrame containing the loaded data
            
        Raises:
            FileNotFoundError: If source doesn't exist
            DataLoadError: If data can't be loaded (corrupted, wrong format)
            
        Example of what a CSV connector might do:
            >>> df = connector.load("users.csv")
            >>> print(df.head())
               username  mfa_enabled    role
            0  alice@...         True   admin
            1    bob@...        False    user
        """
        pass  # 'pass' means "do nothing" - child classes will implement
    
    @abstractmethod
    def validate(self, source: str) -> bool:
        """CHECK if source exists and is readable.
        
        This should be a QUICK check, not a full load.
        
        Args:
            source: Path to validate
            
        Returns:
            True if source can be read, False otherwise
            
        Example:
            >>> if connector.validate("data.csv"):
            ...     print("File exists and looks readable")
            ... else:
            ...     print("File missing or wrong type")
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """GET information about the last loaded source.
        
        After calling load(), this method returns useful info:
        - When was it loaded?
        - How many rows?
        - What columns?
        - File size?
        
        Returns:
            Dictionary with metadata:
            {
                "source": "data.csv",
                "loaded_at": "2024-02-17T15:30:00Z",
                "rows": 1500,
                "columns": ["username", "mfa_enabled", "role"],
                "size_bytes": 45000,
                "connector": "CSVConnector"
            }
        """
        return self._metadata.copy()  # Return a COPY so users can't modify original
    
    def _update_metadata(self, source: str, df: pd.DataFrame, **extra):
        """UPDATE metadata after successful load (PRIVATE method).
        
        The underscore (_) means "internal use only" - don't call this from outside.
        This method is called automatically by load().
        
        Args:
            source: The file that was loaded
            df: The DataFrame that was created
            **extra: Additional metadata (connector-specific)
        """
        # Start with basic metadata
        self._metadata = {
            "source": str(source),
            "loaded_at": datetime.utcnow().isoformat() + "Z",  # 'Z' means UTC
            "rows": len(df),
            "columns": list(df.columns) if not df.empty else [],
            "connector": self.__class__.__name__,
            **extra  # Add any extra fields
        }
        
        # Try to get file size (might fail for non-files like APIs)
        try:
            path = Path(source)
            if path.exists():
                self._metadata["size_bytes"] = path.stat().st_size
        except:
            # If we can't get size, just skip it
            pass
    
    def __str__(self) -> str:
        """STRING representation of this connector.
        
        This is called when you do print(connector) or str(connector).
        
        Returns:
            Human-readable description
        """
        return f"{self.__class__.__name__}(config={self.config})"
    
    def __repr__(self) -> str:
        """REPResentation (for debugging).
        
        Similar to __str__ but more detailed.
        Called when you type the connector name in the Python REPL.
        """
        return f"<{self.__class__.__name__} at {hex(id(self))}>"
