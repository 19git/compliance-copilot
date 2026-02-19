"""Google BigQuery connector for Compliance Copilot."""
import pandas as pd
from typing import Optional, Dict, Any
from google.cloud import bigquery
from google.oauth2 import service_account
from .base import BaseConnector
from .exceptions import DataLoadError

class BigQueryConnector(BaseConnector):
    """Reads data from Google BigQuery."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.project_id = self.config.get('project_id')
        self.dataset_id = self.config.get('dataset_id')
        self.table_id = self.config.get('table_id')
        self.query = self.config.get('query')
        self.credentials_path = self.config.get('credentials_path')
        
        if not self.project_id:
            raise ValueError("BigQueryConnector requires 'project_id' in config")
        
        # Initialize client
        if self.credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = bigquery.Client(
                project=self.project_id,
                credentials=credentials
            )
        else:
            # Use default credentials
            self.client = bigquery.Client(project=self.project_id)
    
    def load(self, source: str = None, **kwargs) -> pd.DataFrame:
        """Load data from BigQuery."""
        try:
            if self.query:
                # Use custom query
                df = self.client.query(self.query).to_dataframe()
            else:
                # Use table reference
                if not self.dataset_id or not self.table_id:
                    raise ValueError("Either 'query' or both 'dataset_id' and 'table_id' must be provided")
                
                table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
                df = self.client.query(f"SELECT * FROM `{table_ref}`").to_dataframe()
            
            self._update_metadata(source or "bigquery", df)
            return df
            
        except Exception as e:
            raise DataLoadError("BigQuery", str(e))
    
    def validate(self, source: str = None) -> bool:
        """Check if BigQuery is accessible."""
        try:
            # Try to list datasets as a connection test
            list(self.client.list_datasets(max_results=1))
            return True
        except:
            return False
    
    def list_datasets(self) -> list:
        """List all datasets in the project."""
        return [dataset.dataset_id for dataset in self.client.list_datasets()]
    
    def list_tables(self, dataset_id: str = None) -> list:
        """List all tables in a dataset."""
        dataset = dataset_id or self.dataset_id
        if not dataset:
            raise ValueError("Dataset ID must be provided")
        
        dataset_ref = self.client.dataset(dataset)
        tables = self.client.list_tables(dataset_ref)
        return [table.table_id for table in tables]
