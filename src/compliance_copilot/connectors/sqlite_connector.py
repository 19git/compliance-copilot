"""SQLite connector for Compliance Copilot."""
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from .base import BaseConnector
from .exceptions import FileNotFoundError, DataLoadError

class SQLiteConnector(BaseConnector):
    """Reads data from SQLite databases."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.database = self.config.get('database')
        self.table = self.config.get('table')
        self.query = self.config.get('query')
        
        if not self.database:
            raise ValueError("SQLiteConnector requires 'database' in config")
    
    def load(self, source: str = None, **kwargs) -> pd.DataFrame:
        """Load data from SQLite table or query."""
        db_path = Path(self.database)
        
        if not db_path.exists():
            raise FileNotFoundError(str(db_path))
        
        try:
            conn = sqlite3.connect(str(db_path))
            
            if self.query:
                # Use custom query
                df = pd.read_sql_query(self.query, conn)
            else:
                # Use table name
                if not self.table:
                    raise ValueError("Either 'table' or 'query' must be provided")
                df = pd.read_sql_query(f"SELECT * FROM {self.table}", conn)
            
            conn.close()
            self._update_metadata(source or self.table or "query", df)
            return df
            
        except Exception as e:
            raise DataLoadError(self.database, str(e))
    
    def validate(self, source: str = None) -> bool:
        """Check if SQLite database exists and is readable."""
        db_path = Path(self.database)
        if not db_path.exists():
            return False
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.close()
            return True
        except:
            return False
    
    def get_tables(self) -> list:
        """List all tables in the database."""
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            raise DataLoadError(self.database, f"Failed to list tables: {e}")
