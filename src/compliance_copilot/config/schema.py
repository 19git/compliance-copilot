"""Configuration schema using Pydantic for validation."""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CSVConnectorConfig(BaseModel):
    delimiter: str = "auto"
    encoding: str = "utf-8"
    header_row: int = Field(0, ge=0)
    
    @validator('delimiter')
    def validate_delimiter(cls, v):
        if v != "auto" and len(v) != 1:
            raise ValueError(f"Delimiter must be single character or 'auto'")
        return v


class ExcelConnectorConfig(BaseModel):
    sheet_name: str = "0"
    header_row: int = Field(0, ge=0)


class PDFConnectorConfig(BaseModel):
    extract_tables: bool = False


class EngineConfig(BaseModel):
    debug: bool = False
    max_violations_per_rule: int = Field(1000, ge=1)
    timeout_seconds: int = Field(30, ge=1)


class ConsoleOutputConfig(BaseModel):
    colorize: bool = True
    show_violations: bool = True


class JSONOutputConfig(BaseModel):
    pretty: bool = True
    include_violations: bool = True


class CSVOutputConfig(BaseModel):
    include_headers: bool = True


class LoggingConfig(BaseModel):
    level: LogLevel = LogLevel.INFO
    directory: str = "logs"


class CacheConfig(BaseModel):
    enabled: bool = True
    directory: str = "cache"
    ttl_seconds: int = Field(3600, ge=0)


class ComplianceConfig(BaseModel):
    engine: EngineConfig = Field(default_factory=EngineConfig)
    connectors: Dict[str, Any] = {
        "csv": CSVConnectorConfig().dict(),
        "excel": ExcelConnectorConfig().dict(),
        "pdf": PDFConnectorConfig().dict()
    }
    output: Dict[str, Any] = {
        "console": ConsoleOutputConfig().dict(),
        "json": JSONOutputConfig().dict(),
        "csv": CSVOutputConfig().dict()
    }
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rules_directories: List[str] = ["rules"]
    data_directories: List[str] = ["data"]
    output_directory: str = "output"
    
    class Config:
        extra = "forbid"
