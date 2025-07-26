#!/usr/bin/env python3
"""
Test script to verify PDF Table Extractor installation and basic functionality.
"""

import sys
import importlib
import os

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing package imports...")
    
    required_packages = [
        'pdfplumber',
        'pandas',
        'numpy',
        'cv2',
        'PIL',
        'flask',
        'flask_cors'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError as e:
            print(f"✗ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\nFailed to import: {failed_imports}")
        print("Please install missing packages using: pip install -r requirements.txt")
        return False
    else:
        print("\nAll packages imported successfully!")
        return True

def test_pdf_extractor():
    """Test if the PDFTableExtractor class can be imported and instantiated."""
    print("\nTesting PDFTableExtractor...")
    
    try:
        from pdf_table_extractor import PDFTableExtractor, TableHeader, ExtractedTable
        print("✓ PDFTableExtractor class imported successfully")
        
        # Test class instantiation (without actual PDF file)
        extractor = PDFTableExtractor("dummy.pdf")
        print("✓ PDFTableExtractor can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"✗ Error importing PDFTableExtractor: {e}")
        return False

def test_flask_app():
    """Test if the Flask app can be imported."""
    print("\nTesting Flask app...")
    
    try:
        from app import app
        print("✓ Flask app imported successfully")
        
        # Test basic app functionality
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ Health endpoint working")
                return True
            else:
                print(f"✗ Health endpoint returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error testing Flask app: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality with sample data."""
    print("\nTesting basic functionality...")
    
    try:
        import pandas as pd
        from pdf_table_extractor import TableHeader, ExtractedTable
        
        # Create sample data
        data = {
            'Name': ['John', 'Jane', 'Bob'],
            'Age': [25, 30, 35],
            'City': ['NYC', 'LA', 'Chicago']
        }
        df = pd.DataFrame(data)
        
        # Create sample headers
        headers = [
            TableHeader(content='Name', level=0, row_index=0),
            TableHeader(content='Age', level=0, row_index=0),
            TableHeader(content='City', level=0, row_index=0)
        ]
        
        # Create sample table
        table = ExtractedTable(
            headers=headers,
            data=df,
            page_number=1,
            table_id='test_table',
            confidence_score=0.95
        )
        
        print("✓ Sample table created successfully")
        print(f"  - Headers: {[h.content for h in table.headers]}")
        print(f"  - Data shape: {table.data.shape}")
        print(f"  - Confidence: {table.confidence_score}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing basic functionality: {e}")
        return False

def test_directories():
    """Test if required directories can be created."""
    print("\nTesting directory creation...")
    
    try:
        directories = ['uploads', 'outputs']
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(directory):
                print(f"✓ Directory '{directory}' created/exists")
            else:
                print(f"✗ Failed to create directory '{directory}'")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating directories: {e}")
        return False

def main():
    """Run all tests."""
    print("PDF Table Extractor - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("PDF Extractor", test_pdf_extractor),
        ("Flask App", test_flask_app),
        ("Basic Functionality", test_basic_functionality),
        ("Directory Creation", test_directories)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"Test '{test_name}' failed!")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Installation is successful.")
        print("\nYou can now:")
        print("1. Run the API server: python app.py")
        print("2. Test with example script: python example_usage.py")
        print("3. Upload a PDF file to extract tables")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Check Python version (requires 3.8+)")
        print("3. Verify file permissions for directory creation")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 