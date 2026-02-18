"""SQL database connector."""

import pandas as pd
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text

from .base import BaseConnector
from .exceptions import DataLoadError


class SQLConnector(BaseConnector):
    """Reads data from SQL databases.
    
    Requires a connection string and a SQL query.
    
    Example config:
        connection_string: "sqlite:///database.db"
        query: "SELECT * FROM users"
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.connection_string = self.config.get("connection_string")
        self.query = self.config.get("query")
        
        if not self.connection_string:
            raise ValueError("SQLConnector requires 'connection_string' in config")
        if not self.query:
            raise ValueError("SQLConnector requires 'query' in config")
    
    def load(self, source: str = None, **kwargs) -> pd.DataFrame:
        """source parameter is ignored; uses config query."""
        try:
            engine = create_engine(self.connection_string)
            df = pd.read_sql(text(self.query), engine)
            self._update_metadata("sql_query", df, query=self.query)
            return df
        except Exception as e:
            raise DataLoadError("SQL query", str(e))
    
    def validate(self, source: str = None) -> bool:
        """Check if we can connect to the database."""
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as conn:
                return True
        except:
            return False
