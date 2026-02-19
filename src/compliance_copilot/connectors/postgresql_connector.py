"""PostgreSQL connector for Compliance Copilot."""
import pandas as pd
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from .base import BaseConnector
from .exceptions import DataLoadError

class PostgreSQLConnector(BaseConnector):
    """Reads data from PostgreSQL databases."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port', 5432)
        self.database = self.config.get('database')
        self.user = self.config.get('user')
        self.password = self.config.get('password')
        self.table = self.config.get('table')
        self.query = self.config.get('query')
        
        if not self.database:
            raise ValueError("PostgreSQLConnector requires 'database' in config")
        
        # Build connection string
        self.connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def load(self, source: str = None, **kwargs) -> pd.DataFrame:
        """Load data from PostgreSQL table or query."""
        try:
            engine = create_engine(self.connection_string)
            
            if self.query:
                # Use custom query
                df = pd.read_sql(text(self.query), engine)
            else:
                # Use table name
                if not self.table:
                    raise ValueError("Either 'table' or 'query' must be provided")
                df = pd.read_sql_table(self.table, engine)
            
            self._update_metadata(source or self.table or "query", df)
            return df
            
        except Exception as e:
            raise DataLoadError(self.database, str(e))
    
    def validate(self, source: str = None) -> bool:
        """Check if PostgreSQL is accessible."""
        try:
            engine = create_engine(self.connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            return False
    
    def get_tables(self) -> list:
        """List all tables in the database."""
        try:
            engine = create_engine(self.connection_string)
            inspector = sqlalchemy.inspect(engine)
            return inspector.get_table_names()
        except Exception as e:
            raise DataLoadError(self.database, f"Failed to list tables: {e}")
