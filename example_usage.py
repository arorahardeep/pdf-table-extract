#!/usr/bin/env python3
"""
Example usage of the PDF Table Extractor

This script demonstrates how to use the PDFTableExtractor class
to extract tables from PDF files with complex headers.
"""

import os
import sys
from pdf_table_extractor import PDFTableExtractor
import pandas as pd

def example_basic_extraction():
    """Basic example of extracting tables from a PDF file."""
    print("=== Basic Table Extraction Example ===")
    
    # Replace with your PDF file path
    pdf_path = "sample_document.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        print("Please provide a valid PDF file path.")
        return
    
    try:
        # Use context manager for automatic cleanup
        with PDFTableExtractor(pdf_path) as extractor:
            # Extract all tables
            tables = extractor.extract_all_tables()
            
            print(f"Found {len(tables)} tables in the PDF")
            
            # Process each table
            for i, table in enumerate(tables):
                print(f"\n--- Table {i+1} ---")
                print(f"Page: {table.page_number}")
                print(f"Table ID: {table.table_id}")
                print(f"Confidence Score: {table.confidence_score:.2f}")
                print(f"Shape: {table.data.shape}")
                
                # Print headers
                if table.headers:
                    print("Headers:")
                    for header in table.headers:
                        print(f"  - {header.content} (Level: {header.level})")
                
                # Print first few rows of data
                if not table.data.empty:
                    print("\nFirst 5 rows of data:")
                    print(table.data.head())
                
                print("-" * 50)
            
            # Get summary
            summary = extractor.get_table_summary(tables)
            print(f"\n=== Summary ===")
            print(f"Total tables: {summary['total_tables']}")
            print(f"Average confidence: {summary['average_confidence']:.2f}")
            print(f"Tables by page: {dict(summary['tables_by_page'])}")
            
    except Exception as e:
        print(f"Error extracting tables: {e}")

def example_export_formats():
    """Example of exporting tables to different formats."""
    print("\n=== Export Formats Example ===")
    
    pdf_path = "sample_document.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    try:
        with PDFTableExtractor(pdf_path) as extractor:
            tables = extractor.extract_all_tables()
            
            if tables:
                # Export to Excel
                excel_path = "extracted_tables.xlsx"
                extractor.export_tables_to_excel(excel_path, tables)
                print(f"Tables exported to Excel: {excel_path}")
                
                # Export to CSV files
                csv_dir = "extracted_tables_csv"
                extractor.export_tables_to_csv(csv_dir, tables)
                print(f"Tables exported to CSV directory: {csv_dir}")
                
    except Exception as e:
        print(f"Error exporting tables: {e}")

def example_advanced_processing():
    """Example of advanced table processing and analysis."""
    print("\n=== Advanced Processing Example ===")
    
    pdf_path = "sample_document.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    try:
        with PDFTableExtractor(pdf_path) as extractor:
            tables = extractor.extract_all_tables()
            
            # Analyze tables with high confidence
            high_confidence_tables = [t for t in tables if t.confidence_score > 0.7]
            print(f"High confidence tables (>0.7): {len(high_confidence_tables)}")
            
            # Find tables with specific header patterns
            for table in tables:
                headers_text = [h.content.lower() for h in table.headers]
                
                # Look for financial tables
                if any(keyword in ' '.join(headers_text) for keyword in ['revenue', 'profit', 'income', 'expense']):
                    print(f"Financial table found: {table.table_id}")
                
                # Look for data tables
                if any(keyword in ' '.join(headers_text) for keyword in ['date', 'name', 'id', 'code']):
                    print(f"Data table found: {table.table_id}")
                
                # Analyze table structure
                if not table.data.empty:
                    print(f"\nTable {table.table_id} structure analysis:")
                    print(f"  - Rows: {len(table.data)}")
                    print(f"  - Columns: {len(table.data.columns)}")
                    print(f"  - Non-null values: {table.data.notna().sum().sum()}")
                    print(f"  - Data types: {table.data.dtypes.value_counts().to_dict()}")
                    
    except Exception as e:
        print(f"Error in advanced processing: {e}")

def example_batch_processing():
    """Example of processing multiple PDF files."""
    print("\n=== Batch Processing Example ===")
    
    # Directory containing PDF files
    pdf_directory = "pdf_files"
    
    if not os.path.exists(pdf_directory):
        print(f"Directory not found: {pdf_directory}")
        return
    
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    all_tables = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        print(f"\nProcessing: {pdf_file}")
        
        try:
            with PDFTableExtractor(pdf_path) as extractor:
                tables = extractor.extract_all_tables()
                all_tables.extend(tables)
                print(f"  - Extracted {len(tables)} tables")
                
        except Exception as e:
            print(f"  - Error processing {pdf_file}: {e}")
    
    print(f"\nTotal tables extracted from all files: {len(all_tables)}")
    
    # Export all tables to a single Excel file
    if all_tables:
        try:
            with PDFTableExtractor("dummy.pdf") as extractor:  # Dummy path for export method
                extractor.export_tables_to_excel("all_extracted_tables.xlsx", all_tables)
                print("All tables exported to: all_extracted_tables.xlsx")
        except Exception as e:
            print(f"Error exporting combined tables: {e}")

def create_sample_pdf():
    """Create a sample PDF with tables for testing (if no PDF is available)."""
    print("\n=== Creating Sample PDF ===")
    
    try:
        # Create a sample DataFrame with complex headers
        data = {
            'Department': ['Sales', 'Marketing', 'Engineering', 'HR'],
            'Q1_Revenue': [100000, 50000, 0, 0],
            'Q2_Revenue': [120000, 60000, 0, 0],
            'Q3_Revenue': [110000, 55000, 0, 0],
            'Q4_Revenue': [130000, 65000, 0, 0],
            'Total_Revenue': [460000, 230000, 0, 0]
        }
        
        df = pd.DataFrame(data)
        
        # Create a multi-level header DataFrame
        multi_header_data = {
            ('Financial', 'Revenue', 'Q1'): [100000, 50000, 0, 0],
            ('Financial', 'Revenue', 'Q2'): [120000, 60000, 0, 0],
            ('Financial', 'Revenue', 'Q3'): [110000, 55000, 0, 0],
            ('Financial', 'Revenue', 'Q4'): [130000, 65000, 0, 0],
            ('Financial', 'Costs', 'Q1'): [80000, 40000, 0, 0],
            ('Financial', 'Costs', 'Q2'): [90000, 45000, 0, 0],
            ('Financial', 'Costs', 'Q3'): [85000, 42000, 0, 0],
            ('Financial', 'Costs', 'Q4'): [95000, 47000, 0, 0],
        }
        
        multi_df = pd.DataFrame(multi_header_data, index=['Sales', 'Marketing', 'Engineering', 'HR'])
        
        print("Sample DataFrames created:")
        print("\nSimple table:")
        print(df)
        print("\nMulti-level header table:")
        print(multi_df)
        
        # Note: Creating actual PDF files requires additional libraries
        # This is just a demonstration of the data structure
        
    except Exception as e:
        print(f"Error creating sample data: {e}")

if __name__ == "__main__":
    print("PDF Table Extractor - Example Usage")
    print("=" * 50)
    
    # Check if sample PDF exists
    if not os.path.exists("sample_document.pdf"):
        print("No sample PDF found. Creating sample data structure...")
        create_sample_pdf()
        print("\nTo test the extractor, please provide a PDF file named 'sample_document.pdf'")
        print("or modify the pdf_path variable in the examples.")
    else:
        # Run examples
        example_basic_extraction()
        example_export_formats()
        example_advanced_processing()
        example_batch_processing()
    
    print("\n" + "=" * 50)
    print("Example usage completed!") 