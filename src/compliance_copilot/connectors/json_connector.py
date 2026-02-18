"""JSON file connector."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from .base import BaseConnector
from .exceptions import FileNotFoundError, DataLoadError, EmptyFileError


class JSONConnector(BaseConnector):
    """Reads JSON files into a pandas DataFrame.
    
    Handles both:
    - JSON array of objects: [{"col1":1}, {"col1":2}]
    - JSON lines format: one JSON object per line
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.encoding = self.config.get("encoding", "utf-8")
        self.lines = self.config.get("lines", False)  # True for JSON lines format
    
    def load(self, source: str, **kwargs) -> pd.DataFrame:
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(str(path))
        
        if path.stat().st_size == 0:
            raise EmptyFileError(str(path))
        
        try:
            # pandas can read JSON directly
            df = pd.read_json(
                path,
                encoding=self.encoding,
                lines=self.lines
            )
            self._update_metadata(source, df)
            return df
        except Exception as e:
            raise DataLoadError(str(path), str(e))
    
    def validate(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() == '.json'
