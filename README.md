# PDF Table Extractor

A powerful Python backend solution for extracting complex tables from PDF documents, with advanced support for multi-line headers and sub-headers.

## Features

- **Advanced Table Detection**: Uses multiple extraction methods including pdfplumber, image processing, and custom algorithms
- **Multi-level Header Processing**: Intelligently detects and consolidates complex headers with sub-headers
- **High Accuracy**: Confidence scoring and multiple extraction strategies for better results
- **Multiple Output Formats**: Export to JSON, Excel, or CSV formats
- **REST API**: Full Flask-based API for easy integration
- **Batch Processing**: Process multiple PDF files simultaneously
- **Table Analysis**: Detailed insights about extracted tables and their structure

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python -c "import pdfplumber, pandas, opencv-python; print('Installation successful!')"
   ```

## Quick Start

### Basic Usage

```python
from pdf_table_extractor import PDFTableExtractor

# Extract tables from a PDF file
with PDFTableExtractor("your_document.pdf") as extractor:
    tables = extractor.extract_all_tables()
    
    for table in tables:
        print(f"Table found on page {table.page_number}")
        print(f"Headers: {[h.content for h in table.headers]}")
        print(f"Data shape: {table.data.shape}")
        print(f"Confidence: {table.confidence_score:.2f}")
```

### Export to Excel

```python
with PDFTableExtractor("your_document.pdf") as extractor:
    tables = extractor.extract_all_tables()
    extractor.export_tables_to_excel("output.xlsx", tables)
```

### Export to CSV

```python
with PDFTableExtractor("your_document.pdf") as extractor:
    tables = extractor.extract_all_tables()
    extractor.export_tables_to_csv("output_directory", tables)
```

## API Usage

### Start the API Server

```bash
python app.py
```

The server will start on `http://localhost:5011`

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

#### 2. Extract Tables from Uploaded File
```bash
POST /extract-tables
```

**Form Data:**
- `file`: PDF file to process
- `output_format`: 'json', 'excel', or 'csv' (optional, default: 'json')
- `include_headers`: boolean (optional, default: true)

**Example using curl:**
```bash
curl -X POST -F "file=@document.pdf" -F "output_format=json" http://localhost:5011/extract-tables
```

#### 3. Extract Tables from URL
```bash
POST /extract-tables-url
```

**JSON Body:**
```json
{
    "pdf_url": "https://example.com/document.pdf",
    "output_format": "json",
    "include_headers": true
}
```

#### 4. Analyze PDF Structure
```bash
POST /analyze-pdf
```

**Form Data:**
- `file`: PDF file to analyze

#### 5. Batch Extract from Multiple Files
```bash
POST /batch-extract
```

**Form Data:**
- `files`: Multiple PDF files
- `output_format`: 'json' or 'excel' (optional, default: 'json')

### API Response Format

#### JSON Response Example
```json
{
    "summary": {
        "total_tables": 3,
        "pages_processed": 2,
        "tables_by_page": {"1": 2, "2": 1},
        "average_confidence": 0.85,
        "table_details": [
            {
                "table_id": "table_1_0",
                "page_number": 1,
                "rows": 10,
                "columns": 5,
                "confidence_score": 0.92,
                "headers": ["Department", "Q1 Revenue", "Q2 Revenue", "Q3 Revenue", "Q4 Revenue"]
            }
        ]
    },
    "tables": [
        {
            "table_id": "table_1_0",
            "page_number": 1,
            "confidence_score": 0.92,
            "headers": ["Department", "Q1 Revenue", "Q2 Revenue", "Q3 Revenue", "Q4 Revenue"],
            "data": [
                {"Department": "Sales", "Q1 Revenue": "100000", "Q2 Revenue": "120000", ...},
                {"Department": "Marketing", "Q1 Revenue": "50000", "Q2 Revenue": "60000", ...}
            ],
            "shape": {"rows": 10, "columns": 5}
        }
    ]
}
```

## Advanced Features

### Multi-level Header Detection

The extractor automatically detects and processes complex headers:

```python
# Example of multi-level header processing
with PDFTableExtractor("complex_table.pdf") as extractor:
    tables = extractor.extract_all_tables()
    
    for table in tables:
        print("Headers with levels:")
        for header in table.headers:
            print(f"  Level {header.level}: {header.content}")
            print(f"  Column span: {header.col_span}, Row span: {header.row_span}")
```

### Confidence Scoring

Each extracted table includes a confidence score (0.0 to 1.0):

```python
# Filter tables by confidence
high_confidence_tables = [t for t in tables if t.confidence_score > 0.8]
```

### Table Analysis

Get detailed insights about extracted tables:

```python
summary = extractor.get_table_summary(tables)
print(f"Total tables: {summary['total_tables']}")
print(f"Average confidence: {summary['average_confidence']:.2f}")
print(f"Tables by page: {dict(summary['tables_by_page'])}")
```

## Example Scripts

### Run the Example Usage Script

```bash
python example_usage.py
```

This will demonstrate various usage patterns and create sample data structures.

### Create a Sample PDF for Testing

If you don't have a PDF file to test with, the example script will create sample data structures to show the expected format.

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
FLASK_ENV=development
FLASK_DEBUG=1
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
```

### API Configuration

Modify `app.py` to change:
- Maximum file size (default: 50MB)
- Upload/output directories
- Server host and port

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **PDF Processing Errors**: Some PDFs may have security restrictions or corrupted content. Try with different PDF files.

3. **Memory Issues**: For large PDFs, consider processing page by page or increasing system memory.

4. **Table Detection Issues**: Complex layouts may require manual adjustment of extraction parameters.

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **Large PDFs**: Process page by page for better memory management
2. **Batch Processing**: Use the batch endpoint for multiple files
3. **Output Format**: Use JSON for API responses, Excel for large datasets
4. **Confidence Filtering**: Filter low-confidence tables to improve quality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the example scripts
3. Test with different PDF files
4. Enable debug logging for detailed error information 