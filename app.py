from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import tempfile
import json
from werkzeug.utils import secure_filename
from pdf_table_extractor import PDFTableExtractor
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle NaN values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if pd.isna(obj) or (isinstance(obj, float) and np.isnan(obj)):
            return None
        return super().default(obj)

app = Flask(__name__)
CORS(app)
app.json_encoder = CustomJSONEncoder

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def clean_data_for_json(data):
    """Clean data to ensure it's JSON serializable."""
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif pd.isna(data) or (isinstance(data, float) and np.isnan(data)):
        return None
    elif isinstance(data, (int, float)):
        # Handle infinity and other special float values
        if np.isinf(data) or np.isnan(data):
            return None
        return data
    else:
        return data

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main HTML interface."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'PDF Table Extractor API'
    })

@app.route('/extract-tables', methods=['POST'])
def extract_tables():
    """
    Extract tables from uploaded PDF file.
    
    Expected form data:
    - file: PDF file to process
    - output_format: 'json', 'excel', or 'csv' (optional, default: 'json')
    - include_headers: boolean (optional, default: True)
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
        
        # Get optional parameters
        output_format = request.form.get('output_format', 'json').lower()
        include_headers = request.form.get('include_headers', 'true').lower() == 'true'
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"{timestamp}_{filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        file.save(temp_path)
        
        logger.info(f"Processing PDF: {filename}")
        
        # Extract tables
        with PDFTableExtractor(temp_path) as extractor:
            tables = extractor.extract_all_tables()
        
        # Get summary
        summary = extractor.get_table_summary(tables)
        
        # Prepare response based on output format
        if output_format == 'json':
            # Generate JSON filename
            json_filename = f"extracted_tables_{timestamp}.json"
            json_path = os.path.join(app.config['OUTPUT_FOLDER'], json_filename)
            
            response_data = {
                'summary': clean_data_for_json(summary),
                'tables': [],
                'filename': json_filename
            }
            
            for table in tables:
                table_data = {
                    'table_id': table.table_id,
                    'page_number': table.page_number,
                    'confidence_score': table.confidence_score,
                    'headers': [h.content for h in table.headers] if include_headers else [],
                    'data': clean_data_for_json(table.data.to_dict('records')) if not table.data.empty else [],
                    'shape': {
                        'rows': len(table.data),
                        'columns': len(table.data.columns)
                    }
                }
                response_data['tables'].append(table_data)
            
            # Save JSON file to output folder
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
                logger.info(f"JSON file saved: {json_path}")
            except Exception as e:
                logger.error(f"Error saving JSON file: {e}")
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return jsonify(response_data)
        
        elif output_format == 'excel':
            # Generate Excel file
            output_filename = f"extracted_tables_{timestamp}.xlsx"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            extractor.export_tables_to_excel(output_path, tables)
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        elif output_format == 'csv':
            # Generate CSV files
            output_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"tables_{timestamp}")
            extractor.export_tables_to_csv(output_dir, tables)
            
            # Create a zip file containing all CSV files
            import zipfile
            zip_filename = f"extracted_tables_{timestamp}.zip"
            zip_path = os.path.join(app.config['OUTPUT_FOLDER'], zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, output_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temporary files
            os.remove(temp_path)
            import shutil
            shutil.rmtree(output_dir)
            
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
        
        else:
            return jsonify({'error': 'Invalid output format. Use "json", "excel", or "csv".'}), 400
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/list-json-files', methods=['GET'])
def list_json_files():
    """List all JSON files in the output folder."""
    try:
        json_files = []
        output_folder = app.config['OUTPUT_FOLDER']
        
        if os.path.exists(output_folder):
            for filename in os.listdir(output_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(output_folder, filename)
                    file_stats = os.stat(file_path)
                    json_files.append({
                        'filename': filename,
                        'size': file_stats.st_size,
                        'created': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
        
        # Sort by modification time (newest first)
        json_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'files': json_files,
            'total_files': len(json_files)
        })
    except Exception as e:
        logger.error(f"Error listing JSON files: {e}")
        return jsonify({'error': f'Error listing files: {str(e)}'}), 500

@app.route('/download-json/<filename>', methods=['GET'])
def download_json(filename):
    """Download a JSON file from the output folder."""
    try:
        json_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(json_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            json_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
    except Exception as e:
        logger.error(f"Error downloading JSON file {filename}: {e}")
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/extract-tables-url', methods=['POST'])
def extract_tables_from_url():
    """
    Extract tables from PDF file accessible via URL.
    
    Expected JSON data:
    {
        "pdf_url": "https://example.com/document.pdf",
        "output_format": "json" (optional),
        "include_headers": true (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'pdf_url' not in data:
            return jsonify({'error': 'PDF URL is required'}), 400
        
        pdf_url = data['pdf_url']
        output_format = data.get('output_format', 'json').lower()
        include_headers = data.get('include_headers', True)
        
        # Download PDF from URL
        import requests
        import tempfile
        
        logger.info(f"Downloading PDF from: {pdf_url}")
        
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        # Extract tables
        with PDFTableExtractor(temp_path) as extractor:
            tables = extractor.extract_all_tables()
        
        # Get summary
        summary = extractor.get_table_summary(tables)
        
        # Prepare response
        response_data = {
            'summary': clean_data_for_json(summary),
            'tables': [],
            'filename': f"extracted_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
        
        for table in tables:
            table_data = {
                'table_id': table.table_id,
                'page_number': table.page_number,
                'confidence_score': table.confidence_score,
                'headers': [h.content for h in table.headers] if include_headers else [],
                'data': clean_data_for_json(table.data.to_dict('records')) if not table.data.empty else [],
                'shape': {
                    'rows': len(table.data),
                    'columns': len(table.data.columns)
                }
            }
            response_data['tables'].append(table_data)
        
        # Save JSON file to output folder
        try:
            json_filename = f"extracted_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_path = os.path.join(app.config['OUTPUT_FOLDER'], json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            logger.info(f"JSON file saved from URL: {json_path}")
        except Exception as e:
            logger.error(f"Error saving JSON file from URL: {e}")
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return jsonify(response_data)
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error downloading PDF: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error processing PDF from URL: {str(e)}")
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/analyze-pdf', methods=['POST'])
def analyze_pdf():
    """
    Analyze PDF structure and provide insights about potential tables.
    
    Expected form data:
    - file: PDF file to analyze
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"{timestamp}_{filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        file.save(temp_path)
        
        # Analyze PDF structure
        with PDFTableExtractor(temp_path) as extractor:
            # Get basic PDF info
            pdf_info = {
                'total_pages': len(extractor.pdf.pages),
                'pages_with_tables': [],
                'estimated_tables': 0
            }
            
            # Analyze each page
            for page_num, page in enumerate(extractor.pdf.pages, 1):
                page_info = {
                    'page_number': page_num,
                    'width': page.width,
                    'height': page.height,
                    'text_blocks': len(page.extract_words()),
                    'potential_tables': 0
                }
                
                # Count potential table areas
                table_areas = extractor._detect_table_areas(page)
                page_info['potential_tables'] = len(table_areas)
                page_info['table_areas'] = table_areas
                
                if page_info['potential_tables'] > 0:
                    pdf_info['pages_with_tables'].append(page_info)
                
                pdf_info['estimated_tables'] += page_info['potential_tables']
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify(pdf_info)
    
    except Exception as e:
        logger.error(f"Error analyzing PDF: {str(e)}")
        return jsonify({'error': f'Error analyzing PDF: {str(e)}'}), 500

@app.route('/batch-extract', methods=['POST'])
def batch_extract():
    """
    Extract tables from multiple PDF files.
    
    Expected form data:
    - files: Multiple PDF files
    - output_format: 'json' or 'excel' (optional, default: 'json')
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        output_format = request.form.get('output_format', 'json').lower()
        
        batch_results = []
        temp_files = []
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
            
            # Save file temporarily
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_filename = f"{timestamp}_{filename}"
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            
            file.save(temp_path)
            temp_files.append(temp_path)
            
            # Extract tables
            try:
                with PDFTableExtractor(temp_path) as extractor:
                    tables = extractor.extract_all_tables()
                
                summary = extractor.get_table_summary(tables)
                
                file_result = {
                    'filename': filename,
                    'summary': clean_data_for_json(summary),
                    'tables': []
                }
                
                for table in tables:
                    table_data = {
                        'table_id': table.table_id,
                        'page_number': table.page_number,
                        'confidence_score': table.confidence_score,
                        'headers': [h.content for h in table.headers],
                        'data': clean_data_for_json(table.data.to_dict('records')) if not table.data.empty else [],
                        'shape': {
                            'rows': len(table.data),
                            'columns': len(table.data.columns)
                        }
                    }
                    file_result['tables'].append(table_data)
                
                batch_results.append(file_result)
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                batch_results.append({
                    'filename': filename,
                    'error': str(e)
                })
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        if output_format == 'excel':
            # Create Excel file with multiple sheets
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"batch_extracted_tables_{timestamp}.xlsx"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for file_result in batch_results:
                    if 'error' not in file_result:
                        for table in file_result['tables']:
                            sheet_name = f"{file_result['filename'][:20]}_{table['table_id']}"
                            if len(sheet_name) > 31:
                                sheet_name = sheet_name[:31]
                            
                            df = pd.DataFrame(table['data'])
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        else:
            return jsonify({
                'total_files': len(batch_results),
                'successful_extractions': len([r for r in batch_results if 'error' not in r]),
                'results': batch_results
            })
    
    except Exception as e:
        logger.error(f"Error in batch extraction: {str(e)}")
        return jsonify({'error': f'Error in batch extraction: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5011) 