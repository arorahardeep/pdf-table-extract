#!/usr/bin/env python3
"""
Setup script for PDF Table Extractor
Automates installation and initial setup.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Check if pip is available
    if not shutil.which('pip'):
        print("❌ pip not found. Please install pip first.")
        return False
    
    # Install dependencies from requirements.txt
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        'uploads',
        'outputs',
        'templates'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def run_tests():
    """Run installation tests."""
    print("\n🧪 Running installation tests...")
    
    if not run_command("python test_installation.py", "Running installation tests"):
        return False
    
    return True

def create_sample_files():
    """Create sample files for testing."""
    print("\n📄 Creating sample files...")
    
    # Create a simple sample PDF info file
    sample_info = """
Sample PDF Files for Testing:

To test the PDF Table Extractor, you can use any PDF file that contains tables.
Here are some suggestions for finding sample PDFs:

1. Financial Reports (annual reports, quarterly reports)
2. Research Papers with data tables
3. Government documents with statistical tables
4. Business reports with performance metrics
5. Academic papers with experimental results

You can find sample PDFs from:
- Company websites (investor relations sections)
- Government websites (statistics and reports)
- Academic repositories
- Research paper databases

Place your PDF files in the project directory and run:
python example_usage.py

 Or use the web interface by running:
 python run.py
 Then visit: http://localhost:5011
"""
    
    try:
        with open('SAMPLE_FILES_INFO.txt', 'w') as f:
            f.write(sample_info)
        print("✅ Created sample files info")
    except Exception as e:
        print(f"❌ Failed to create sample files info: {e}")
    
    return True

def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("🎉 PDF Table Extractor Setup Complete!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Get a PDF file with tables for testing")
    print("2. Run the web interface:")
    print("   python run.py")
    print("3. Open your browser and go to: http://localhost:5011")
    print("4. Upload your PDF and extract tables!")
    
    print("\n🔧 Alternative Usage:")
    print("• Run example script: python example_usage.py")
    print("• Use as Python library: from pdf_table_extractor import PDFTableExtractor")
    print("• API endpoints available at: http://localhost:5011/health")
    
    print("\n📚 Documentation:")
    print("• Read README.md for detailed usage instructions")
    print("• Check example_usage.py for code examples")
    print("• API documentation in README.md")
    
    print("\n🆘 Troubleshooting:")
    print("• Run: python test_installation.py")
    print("• Check logs in: pdf_extractor.log")
    print("• Ensure all dependencies are installed: pip install -r requirements.txt")

def main():
    """Main setup function."""
    print("🚀 PDF Table Extractor - Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed. Please check the errors above.")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Directory creation failed. Please check the errors above.")
        sys.exit(1)
    
    # Create sample files
    create_sample_files()
    
    # Run tests
    if not run_tests():
        print("\n⚠️  Some tests failed. The installation may still work, but please check the errors above.")
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main() 