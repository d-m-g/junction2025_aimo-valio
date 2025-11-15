"""
Configuration management for NLU Parser
Supports environment variables and config file
"""

import os
from pathlib import Path
from typing import Dict, Optional

# Default configuration
DEFAULT_CONFIG = {
    'api': {
        'host': '0.0.0.0',
        'port': 5000,
        'debug': False,
    },
    'cors': {
        'enabled': True,
        'origins': '*',  # '*' for all, or list of origins
    },
    'validation': {
        'min_text_length': 1,
        'max_text_length': 5000,
        'max_batch_size': 100,
    },
    'confidence': {
        'min_intent_confidence': 0.3,
        'min_entity_confidence': 0.4,
        'uncertain_threshold': 0.6,
    },
    'nlu': {
        'use_semantic_fallback': True,
        'semantic_threshold': 0.5,  # Use semantic if rule-based confidence < this
        'semantic_weight': 0.8,  # Weight for semantic scores vs rule scores
    },
    'product_matching': {
        'fuzzy_threshold': 0.7,
        'max_fuzzy_results': 5,
    },
    'session': {
        'enabled': True,
        'max_history': 10,
        'ttl_seconds': 3600,  # 1 hour
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    },
    'paths': {
        'data_dir': None,  # Auto-detected
    }
}


class Config:
    """Configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Optional path to config file (JSON/YAML)
        """
        self._config = DEFAULT_CONFIG.copy()
        self._load_from_env()
        if config_file:
            self._load_from_file(config_file)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # API config
        if os.getenv('NLU_HOST'):
            self._config['api']['host'] = os.getenv('NLU_HOST')
        if os.getenv('NLU_PORT'):
            self._config['api']['port'] = int(os.getenv('NLU_PORT'))
        if os.getenv('NLU_DEBUG'):
            self._config['api']['debug'] = os.getenv('NLU_DEBUG').lower() == 'true'
        
        # CORS config
        if os.getenv('NLU_CORS_ORIGINS'):
            origins = os.getenv('NLU_CORS_ORIGINS')
            self._config['cors']['origins'] = [o.strip() for o in origins.split(',')]
        
        # Validation config
        if os.getenv('NLU_MAX_TEXT_LENGTH'):
            self._config['validation']['max_text_length'] = int(os.getenv('NLU_MAX_TEXT_LENGTH'))
        if os.getenv('NLU_MAX_BATCH_SIZE'):
            self._config['validation']['max_batch_size'] = int(os.getenv('NLU_MAX_BATCH_SIZE'))
        
        # Confidence thresholds
        if os.getenv('NLU_MIN_INTENT_CONFIDENCE'):
            self._config['confidence']['min_intent_confidence'] = float(os.getenv('NLU_MIN_INTENT_CONFIDENCE'))
        if os.getenv('NLU_MIN_ENTITY_CONFIDENCE'):
            self._config['confidence']['min_entity_confidence'] = float(os.getenv('NLU_MIN_ENTITY_CONFIDENCE'))
        
        # Semantic classifier config
        if os.getenv('NLU_USE_SEMANTIC_FALLBACK'):
            self._config['nlu']['use_semantic_fallback'] = os.getenv('NLU_USE_SEMANTIC_FALLBACK').lower() == 'true'
        if os.getenv('NLU_SEMANTIC_THRESHOLD'):
            self._config['nlu']['semantic_threshold'] = float(os.getenv('NLU_SEMANTIC_THRESHOLD'))
        if os.getenv('NLU_SEMANTIC_WEIGHT'):
            self._config['nlu']['semantic_weight'] = float(os.getenv('NLU_SEMANTIC_WEIGHT'))
    
    def _load_from_file(self, config_file: str):
        """Load configuration from file (future: support JSON/YAML)"""
        # TODO: Implement file loading
        pass
    
    def get(self, key_path: str, default=None):
        """
        Get config value by dot-separated path
        
        Args:
            key_path: Dot-separated path (e.g., 'api.port')
            default: Default value if not found
            
        Returns:
            Config value or default
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_all(self) -> Dict:
        """Get all configuration"""
        return self._config.copy()


# Global config instance
config = Config()

