"""MongoDB connector for Compliance Copilot."""
import pandas as pd
from typing import Optional, Dict, Any
from pymongo import MongoClient
from .base import BaseConnector
from .exceptions import DataLoadError

class MongoDBConnector(BaseConnector):
    """Reads data from MongoDB collections."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.connection_string = self.config.get('connection_string', 'mongodb://localhost:27017/')
        self.database = self.config.get('database')
        self.collection = self.config.get('collection')
        self.query = self.config.get('query', {})
        self.project = self.config.get('project', None)
        
        if not self.database or not self.collection:
            raise ValueError("MongoDBConnector requires 'database' and 'collection' in config")
    
    def load(self, source: str = None, **kwargs) -> pd.DataFrame:
        """Load data from MongoDB collection."""
        try:
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            db = client[self.database]
            coll = db[self.collection]
            
            # Execute query with optional projection
            cursor = coll.find(self.query, self.project)
            df = pd.DataFrame(list(cursor))
            
            # Convert ObjectId to string for JSON serialization
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            
            client.close()
            self._update_metadata(source or f"{self.database}.{self.collection}", df)
            return df
            
        except Exception as e:
            raise DataLoadError(f"{self.database}.{self.collection}", str(e))
    
    def validate(self, source: str = None) -> bool:
        """Check if MongoDB is accessible."""
        try:
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            client.server_info()
            client.close()
            return True
        except:
            return False
    
    def get_collections(self) -> list:
        """List all collections in the database."""
        try:
            client = MongoClient(self.connection_string)
            db = client[self.database]
            return db.list_collection_names()
        except Exception as e:
            raise DataLoadError(self.database, f"Failed to list collections: {e}")
