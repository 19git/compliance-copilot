"""Excel file connector."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Union

from .base import BaseConnector
from .exceptions import FileNotFoundError, DataLoadError


class ExcelConnector(BaseConnector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.sheet_name = self.config.get("sheet_name", 0)
        self.header_row = self.config.get("header_row", 0)
    
    def load(self, source: str, sheet_name: Optional[Union[str, int]] = None, **kwargs) -> pd.DataFrame:
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(str(path))
        
        sheet = sheet_name if sheet_name is not None else self.sheet_name
        
        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                header=self.header_row
            )
            self._update_metadata(source, df, sheet_name=str(sheet))
            return df
        except ValueError as e:
            if "No sheet named" in str(e):
                sheets = self.get_sheets(source)
                raise DataLoadError(
                    str(path),
                    f"Sheet '{sheet}' not found. Available: {', '.join(sheets)}"
                )
            raise DataLoadError(str(path), str(e))
        except Exception as e:
            raise DataLoadError(str(path), str(e))
    
    def validate(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() in ['.xlsx', '.xls']
    
    def get_sheets(self, source: str) -> list:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(str(path))
        return pd.ExcelFile(path).sheet_names
