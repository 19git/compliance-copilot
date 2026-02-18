"""Basic PDF text connector."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from .base import BaseConnector
from .exceptions import FileNotFoundError, DataLoadError


class PDFConnector(BaseConnector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        
        try:
            import PyPDF2
            self.PyPDF2 = PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")
    
    def load(self, source: str, **kwargs) -> pd.DataFrame:
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(str(path))
        
        try:
            with open(path, 'rb') as f:
                reader = self.PyPDF2.PdfReader(f)
                pages = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append({'page': i + 1, 'text': text.strip()})
                
                df = pd.DataFrame(pages) if pages else pd.DataFrame([{'page': 1, 'text': ''}])
                self._update_metadata(source, df)
                return df
        except Exception as e:
            raise DataLoadError(str(path), str(e))
    
    def validate(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() == '.pdf'
