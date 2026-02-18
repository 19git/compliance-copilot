"""Configuration loader that merges multiple sources."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from .schema import ComplianceConfig
from ..exceptions import ConfigFileNotFoundError, ConfigSyntaxError


class ConfigLoader:
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.cwd()
        self.package_dir = Path(__file__).parent.parent
        
        env_file = self.config_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    
    def load(self, config_file: str = "config.yaml") -> ComplianceConfig:
        config_dict = self._load_defaults()
        
        user_config = self._load_user_config(config_file)
        if user_config:
            config_dict = self._deep_merge(config_dict, user_config)
        
        env_config = self._load_from_env()
        if env_config:
            config_dict = self._deep_merge(config_dict, env_config)
        
        return ComplianceConfig(**config_dict)
    
    def _load_defaults(self) -> Dict[str, Any]:
        defaults_path = self.package_dir / "config" / "defaults.yaml"
        if not defaults_path.exists():
            raise ConfigFileNotFoundError(str(defaults_path))
        
        with open(defaults_path, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigSyntaxError(str(defaults_path), 0, str(e))
    
    def _load_user_config(self, config_file: str) -> Optional[Dict[str, Any]]:
        config_path = self.config_dir / config_file
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigSyntaxError(str(config_path), 0, str(e))
    
    def _load_from_env(self) -> Dict[str, Any]:
        config = {}
        prefix = "COMPLIANCE_"
        
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            
            path = key[len(prefix):].lower().split('__')
            typed_value = self._convert_type(value)
            
            current = config
            for part in path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[path[-1]] = typed_value
        
        return config
    
    def _convert_type(self, value: str) -> Any:
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        if value.lower() in ('false', 'no', 'off', '0'):
            return False
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
