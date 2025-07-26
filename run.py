#!/usr/bin/env python3
"""
Startup script for the PDF Table Extractor Flask application.
"""

import os
import sys
import logging
from app import app
from config import get_config

def setup_logging():
    """Setup logging configuration."""
    config = get_config()
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
        ]
    )

def create_directories():
    """Create necessary directories if they don't exist."""
    config = get_config()
    
    directories = [config.UPLOAD_FOLDER, config.OUTPUT_FOLDER]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Directory '{directory}' ready")
        except Exception as e:
            print(f"✗ Error creating directory '{directory}': {e}")
            return False
    
    return True

def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = [
        'pdfplumber',
        'pandas',
        'numpy',
        'cv2',
        'flask',
        'flask_cors'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"✗ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install -r requirements.txt")
        return False
    
    print("✓ All dependencies available")
    return True

def main():
    """Main startup function."""
    print("PDF Table Extractor - Starting Server")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Get configuration
    config = get_config()
    
    # Configure Flask app
    app.config.from_object(config)
    
    # Get server settings
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5011))
    debug = config.DEBUG
    
    print(f"\nServer Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Debug: {debug}")
    print(f"  Upload folder: {config.UPLOAD_FOLDER}")
    print(f"  Output folder: {config.OUTPUT_FOLDER}")
    print(f"  Max file size: {config.MAX_CONTENT_LENGTH / (1024*1024):.1f} MB")
    
    print(f"\nStarting server...")
    print(f"API will be available at: http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the Flask application
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n✗ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 