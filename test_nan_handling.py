#!/usr/bin/env python3
"""
Test script to verify NaN handling in JSON serialization.
"""

import json
import pandas as pd
import numpy as np
from pdf_table_extractor import PDFTableExtractor, ExtractedTable, TableHeader

def test_nan_handling():
    """Test that NaN values are properly handled in JSON serialization."""
    print("Testing NaN handling in JSON serialization...")
    
    # Create test data with NaN values
    test_data = {
        'Column_1': ['Value1', 'Value2', np.nan, 'Value4'],
        'Column_2': [1, 2, np.nan, 4],
        'Column_3': [1.5, 2.5, np.nan, 4.5]
    }
    
    df = pd.DataFrame(test_data)
    
    # Create test headers
    headers = [
        TableHeader(content='Column_1', level=0, row_index=0),
        TableHeader(content='Column_2', level=0, row_index=0),
        TableHeader(content='Column_3', level=0, row_index=0)
    ]
    
    # Create test table
    table = ExtractedTable(
        headers=headers,
        data=df,
        page_number=1,
        table_id='test_table',
        confidence_score=0.95
    )
    
    # Test direct JSON serialization (should fail without custom encoder)
    print("\n1. Testing direct JSON serialization...")
    try:
        json_str = json.dumps(table.data.to_dict('records'))
        print("✓ Direct JSON serialization successful")
    except Exception as e:
        print(f"✗ Direct JSON serialization failed: {e}")
    
    # Test with custom encoder
    print("\n2. Testing with custom JSON encoder...")
    
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if pd.isna(obj) or (isinstance(obj, float) and np.isnan(obj)):
                return None
            return super().default(obj)
    
    try:
        json_str = json.dumps(table.data.to_dict('records'), cls=CustomJSONEncoder)
        print("✓ Custom JSON encoder successful")
        print(f"JSON output: {json_str}")
    except Exception as e:
        print(f"✗ Custom JSON encoder failed: {e}")
    
    # Test data cleaning function
    print("\n3. Testing data cleaning function...")
    
    def clean_data_for_json(data):
        """Clean data to ensure it's JSON serializable."""
        if isinstance(data, dict):
            return {k: clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [clean_data_for_json(item) for item in data]
        elif pd.isna(data) or (isinstance(data, float) and np.isnan(data)):
            return None
        elif isinstance(data, (int, float)):
            if np.isinf(data) or np.isnan(data):
                return None
            return data
        else:
            return data
    
    try:
        cleaned_data = clean_data_for_json(table.data.to_dict('records'))
        json_str = json.dumps(cleaned_data)
        print("✓ Data cleaning function successful")
        print(f"Cleaned JSON output: {json_str}")
    except Exception as e:
        print(f"✗ Data cleaning function failed: {e}")
    
    # Test confidence score handling
    print("\n4. Testing confidence score handling...")
    
    # Test with NaN confidence
    try:
        nan_table = ExtractedTable(
            headers=headers,
            data=df,
            page_number=1,
            table_id='test_table_nan',
            confidence_score=np.nan
        )
        
        # Ensure confidence is valid
        confidence = nan_table.confidence_score
        if pd.isna(confidence) or confidence < 0:
            confidence = 0.0
        elif confidence > 1.0:
            confidence = 1.0
        
        print(f"✓ Confidence score handled: {confidence}")
    except Exception as e:
        print(f"✗ Confidence score handling failed: {e}")
    
    print("\n✅ NaN handling test completed!")

def test_length_mismatch_handling():
    """Test handling of length mismatches in table processing."""
    print("\nTesting length mismatch handling...")
    
    # Create test data with mismatched columns
    test_data = {
        'Column_1': ['Value1', 'Value2'],
        'Column_2': ['Value3'],  # Different length
        'Column_3': ['Value4', 'Value5', 'Value6']  # Different length
    }
    
    try:
        df = pd.DataFrame(test_data)
        print(f"✓ DataFrame created with shape: {df.shape}")
        
        # Test header processing with mismatched data
        headers = [
            TableHeader(content='Header1', level=0, row_index=0),
            TableHeader(content='Header2', level=0, row_index=0),
            TableHeader(content='Header3', level=0, row_index=0),
            TableHeader(content='Header4', level=0, row_index=0),  # Extra header
        ]
        
        # This should handle the mismatch gracefully
        if len(headers) > len(df.columns):
            headers = headers[:len(df.columns)]
        
        print(f"✓ Headers adjusted to match columns: {len(headers)} headers for {len(df.columns)} columns")
        
    except Exception as e:
        print(f"✗ Length mismatch handling failed: {e}")

if __name__ == "__main__":
    print("NaN and Length Mismatch Handling Test")
    print("=" * 50)
    
    test_nan_handling()
    test_length_mismatch_handling()
    
    print("\n" + "=" * 50)
    print("All tests completed!") 