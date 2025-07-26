"""
Configuration settings for the PDF Table Extractor.
"""

import os
from typing import Dict, Any

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', 'outputs')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # PDF processing settings
    PDF_PROCESSING_TIMEOUT = int(os.environ.get('PDF_PROCESSING_TIMEOUT', 300))  # 5 minutes
    MAX_PAGES_PER_PDF = int(os.environ.get('MAX_PAGES_PER_PDF', 100))
    
    # Table extraction settings
    MIN_TABLE_CONFIDENCE = float(os.environ.get('MIN_TABLE_CONFIDENCE', 0.3))
    MAX_TABLES_PER_PAGE = int(os.environ.get('MAX_TABLES_PER_PAGE', 10))
    
    # Image processing settings
    TABLE_AREA_MIN_SIZE = int(os.environ.get('TABLE_AREA_MIN_SIZE', 1000))
    EDGE_DETECTION_LOW = int(os.environ.get('EDGE_DETECTION_LOW', 50))
    EDGE_DETECTION_HIGH = int(os.environ.get('EDGE_DETECTION_HIGH', 150))
    
    # Header detection settings
    HEADER_DETECTION_THRESHOLD = float(os.environ.get('HEADER_DETECTION_THRESHOLD', 0.6))
    MAX_HEADER_ROWS = int(os.environ.get('MAX_HEADER_ROWS', 5))
    
    # API settings
    API_RATE_LIMIT = os.environ.get('API_RATE_LIMIT', '100 per minute')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'pdf_extractor.log')
    
    # Database settings (for future use)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    @classmethod
    def get_table_extraction_settings(cls) -> Dict[str, Any]:
        """Get settings specific to table extraction."""
        return {
            'min_confidence': cls.MIN_TABLE_CONFIDENCE,
            'max_tables_per_page': cls.MAX_TABLES_PER_PAGE,
            'header_detection_threshold': cls.HEADER_DETECTION_THRESHOLD,
            'max_header_rows': cls.MAX_HEADER_ROWS,
            'table_area_min_size': cls.TABLE_AREA_MIN_SIZE,
            'edge_detection_low': cls.EDGE_DETECTION_LOW,
            'edge_detection_high': cls.EDGE_DETECTION_HIGH
        }
    
    @classmethod
    def get_flask_settings(cls) -> Dict[str, Any]:
        """Get Flask-specific settings."""
        return {
            'secret_key': cls.SECRET_KEY,
            'debug': cls.DEBUG,
            'max_content_length': cls.MAX_CONTENT_LENGTH,
            'upload_folder': cls.UPLOAD_FOLDER,
            'output_folder': cls.OUTPUT_FOLDER
        }

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # Production-specific settings
    MIN_TABLE_CONFIDENCE = 0.5
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Testing-specific settings
    UPLOAD_FOLDER = 'test_uploads'
    OUTPUT_FOLDER = 'test_outputs'
    MIN_TABLE_CONFIDENCE = 0.1

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """Get configuration based on environment."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default']) 