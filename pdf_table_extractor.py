import pdfplumber
import pandas as pd
import numpy as np
import cv2
from PIL import Image
import io
import re
from typing import List, Dict, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TableHeader:
    """Represents a table header with its hierarchy level and content."""
    content: str
    level: int
    row_index: int
    col_span: int = 1
    row_span: int = 1

@dataclass
class ExtractedTable:
    """Represents an extracted table with processed headers and data."""
    headers: List[TableHeader]
    data: pd.DataFrame
    page_number: int
    table_id: str
    confidence_score: float

class PDFTableExtractor:
    """
    Advanced PDF table extractor that can handle complex tables with multi-line headers
    and sub-headers.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = None
        self.tables = []
        
    def __enter__(self):
        self.pdf = pdfplumber.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf:
            self.pdf.close()
    
    def extract_all_tables(self) -> List[ExtractedTable]:
        """Extract all tables from the PDF with processed headers."""
        extracted_tables = []
        
        for page_num, page in enumerate(self.pdf.pages, 1):
            logger.info(f"Processing page {page_num}")
            
            # Extract tables using multiple methods
            tables = self._extract_tables_from_page(page, page_num)
            
            for table_idx, table in enumerate(tables):
                try:
                    processed_table = self._process_table(table, page_num, table_idx)
                    if processed_table:
                        extracted_tables.append(processed_table)
                except Exception as e:
                    logger.error(f"Error processing table {table_idx} on page {page_num}: {e}")
                    continue
        
        return extracted_tables
    
    def _extract_tables_from_page(self, page, page_num: int) -> List:
        """Extract tables from a single page using multiple extraction methods."""
        tables = []
        
        # Method 1: pdfplumber's built-in table finder
        try:
            pdfplumber_tables = page.find_tables()
            tables.extend(pdfplumber_tables)
        except Exception as e:
            logger.warning(f"pdfplumber table extraction failed on page {page_num}: {e}")
        
        # Method 2: Extract tables using table settings
        try:
            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "intersection_y_tolerance": 10,
                "intersection_x_tolerance": 10
            }
            custom_tables = page.find_tables(table_settings)
            tables.extend(custom_tables)
        except Exception as e:
            logger.warning(f"Custom table extraction failed on page {page_num}: {e}")
        
        # Method 3: Extract using explicit table areas
        try:
            # Look for table-like structures in the page
            table_areas = self._detect_table_areas(page)
            for area in table_areas:
                cropped_page = page.within_bbox(area)
                area_tables = cropped_page.find_tables()
                tables.extend(area_tables)
        except Exception as e:
            logger.warning(f"Table area detection failed on page {page_num}: {e}")
        
        return tables
    
    def _detect_table_areas(self, page) -> List[Tuple[float, float, float, float]]:
        """Detect potential table areas on the page using image processing."""
        areas = []
        
        try:
            # Convert page to image
            img = page.to_image()
            img_array = np.array(img.original)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours that might be tables
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    # Convert to page coordinates
                    page_x = x / img_array.shape[1] * page.width
                    page_y = y / img_array.shape[0] * page.height
                    page_w = w / img_array.shape[1] * page.width
                    page_h = h / img_array.shape[0] * page.height
                    
                    areas.append((page_x, page_y, page_x + page_w, page_y + page_h))
                    
        except Exception as e:
            logger.warning(f"Table area detection failed: {e}")
        
        return areas
    
    def _process_table(self, table, page_num: int, table_idx: int) -> Optional[ExtractedTable]:
        """Process a raw table and extract headers and data."""
        try:
            if not table or not table.extract():
                return None
            
            # Convert table to DataFrame
            df = pd.DataFrame(table.extract())
            
            if df.empty:
                return None
            
            # Detect and process headers
            headers = self._detect_and_process_headers(df)
            
            # Create clean data DataFrame
            clean_data = self._create_clean_dataframe(df, headers)
            
            # Calculate confidence score with error handling
            try:
                confidence = self._calculate_confidence_score(df, headers)
                # Ensure confidence is a valid number
                if pd.isna(confidence) or confidence < 0:
                    confidence = 0.0
                elif confidence > 1.0:
                    confidence = 1.0
            except Exception as e:
                logger.warning(f"Error calculating confidence score: {e}")
                confidence = 0.0
            
            return ExtractedTable(
                headers=headers,
                data=clean_data,
                page_number=page_num,
                table_id=f"table_{page_num}_{table_idx}",
                confidence_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Error processing table {table_idx} on page {page_num}: {e}")
            # Return a minimal table with error information
            try:
                return ExtractedTable(
                    headers=[],
                    data=pd.DataFrame(),
                    page_number=page_num,
                    table_id=f"table_{page_num}_{table_idx}_error",
                    confidence_score=0.0
                )
            except:
                return None
    
    def _detect_and_process_headers(self, df: pd.DataFrame) -> List[TableHeader]:
        """Detect and process multi-level headers from the DataFrame."""
        headers = []
        
        # Analyze the first few rows to detect header patterns
        header_rows = self._identify_header_rows(df)
        
        for row_idx in header_rows:
            row_headers = self._process_header_row(df.iloc[row_idx], row_idx, header_rows)
            headers.extend(row_headers)
        
        # Merge and consolidate headers
        consolidated_headers = self._consolidate_headers(headers)
        
        return consolidated_headers
    
    def _identify_header_rows(self, df: pd.DataFrame) -> List[int]:
        """Identify which rows contain headers based on content patterns."""
        header_rows = []
        
        # Check first few rows for header characteristics
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            
            # Check if row has header-like characteristics
            if self._is_header_row(row):
                header_rows.append(i)
            else:
                # Stop at first non-header row
                break
        
        return header_rows
    
    def _is_header_row(self, row) -> bool:
        """Determine if a row is likely a header row."""
        # Count non-empty cells
        non_empty = sum(1 for cell in row if cell and str(cell).strip())
        
        # Check for header-like patterns
        header_indicators = 0
        
        for cell in row:
            if cell:
                cell_str = str(cell).strip()
                
                # Check for common header patterns
                if (cell_str.isupper() or 
                    any(keyword in cell_str.lower() for keyword in ['total', 'sum', 'count', 'name', 'date', 'id']) or
                    len(cell_str.split()) <= 3):  # Short phrases are often headers
                    header_indicators += 1
        
        # Row is likely a header if most cells show header characteristics
        return header_indicators >= non_empty * 0.6
    
    def _process_header_row(self, row, row_idx: int, header_rows: List[int]) -> List[TableHeader]:
        """Process a single header row and extract headers."""
        headers = []
        
        for col_idx, cell in enumerate(row):
            if cell and str(cell).strip():
                # Determine header level based on position in header hierarchy
                level = header_rows.index(row_idx)
                
                # Check for merged cells
                col_span = self._detect_column_span(row, col_idx)
                row_span = self._detect_row_span(header_rows, row_idx)
                
                header = TableHeader(
                    content=str(cell).strip(),
                    level=level,
                    row_index=row_idx,
                    col_span=col_span,
                    row_span=row_span
                )
                headers.append(header)
        
        return headers
    
    def _detect_column_span(self, row, col_idx: int) -> int:
        """Detect if a header spans multiple columns."""
        span = 1
        current_cell = row.iloc[col_idx]
        
        # Check subsequent columns for similar content
        for i in range(col_idx + 1, len(row)):
            if row.iloc[i] == current_cell or not row.iloc[i]:
                span += 1
            else:
                break
        
        return span
    
    def _detect_row_span(self, header_rows: List[int], row_idx: int) -> int:
        """Detect if a header spans multiple rows."""
        # For now, assume single row span
        # This could be enhanced with more sophisticated detection
        return 1
    
    def _consolidate_headers(self, headers: List[TableHeader]) -> List[TableHeader]:
        """Consolidate multi-level headers into a single comprehensive header."""
        consolidated = []
        
        # Group headers by column position
        header_groups = defaultdict(list)
        for header in headers:
            # Use a simple column position for grouping
            col_pos = len(header_groups)
            header_groups[col_pos].append(header)
        
        # Consolidate each group
        for col_pos, group in header_groups.items():
            if group:
                # Sort by level
                group.sort(key=lambda h: h.level)
                
                # Combine header content
                combined_content = " - ".join([h.content for h in group])
                
                # Create consolidated header
                consolidated_header = TableHeader(
                    content=combined_content,
                    level=0,  # Top level after consolidation
                    row_index=min(h.row_index for h in group),
                    col_span=1,
                    row_span=1
                )
                
                consolidated.append(consolidated_header)
        
        return consolidated
    
    def _create_clean_dataframe(self, df: pd.DataFrame, headers: List[TableHeader]) -> pd.DataFrame:
        """Create a clean DataFrame with proper headers and data."""
        try:
            # Find the last header row
            if headers:
                last_header_row = max(h.row_index for h in headers)
                data_start_row = last_header_row + 1
            else:
                data_start_row = 0
            
            # Extract data rows
            if data_start_row < len(df):
                data_df = df.iloc[data_start_row:].copy()
            else:
                data_df = pd.DataFrame()
            
            # Handle column mismatch gracefully
            if headers and len(headers) > 0:
                # Ensure we don't exceed the number of columns in the data
                max_columns = min(len(headers), len(data_df.columns) if not data_df.empty else 0)
                
                if max_columns > 0:
                    # Create column names from headers
                    column_names = [h.content for h in headers[:max_columns]]
                    
                    # If we have fewer headers than columns, create generic names for remaining columns
                    if len(column_names) < len(data_df.columns):
                        for i in range(len(column_names), len(data_df.columns)):
                            column_names.append(f"Column_{i+1}")
                    
                    # Set column names
                    data_df.columns = column_names
                else:
                    # No valid headers, create generic column names
                    if not data_df.empty:
                        data_df.columns = [f"Column_{i+1}" for i in range(len(data_df.columns))]
            
            # Clean the data
            data_df = self._clean_dataframe(data_df)
            
            return data_df
            
        except Exception as e:
            logger.warning(f"Error creating clean dataframe: {e}")
            # Return empty dataframe with generic columns as fallback
            if not df.empty:
                fallback_df = df.copy()
                fallback_df.columns = [f"Column_{i+1}" for i in range(len(fallback_df.columns))]
                return self._clean_dataframe(fallback_df)
            return pd.DataFrame()
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the DataFrame by removing empty rows and columns."""
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Clean cell values
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace empty strings with NaN
            df[col] = df[col].replace('', np.nan)
        
        return df
    
    def _calculate_confidence_score(self, df: pd.DataFrame, headers: List[TableHeader]) -> float:
        """Calculate a confidence score for the table extraction."""
        score = 0.0
        
        # Base score for having data
        if not df.empty:
            score += 0.3
        
        # Score for having headers
        if headers:
            score += 0.3
        
        # Score for data quality (non-empty cells)
        if not df.empty:
            non_empty_ratio = df.notna().sum().sum() / (df.shape[0] * df.shape[1])
            score += non_empty_ratio * 0.2
        
        # Score for table structure (consistent number of columns)
        if not df.empty:
            col_counts = df.notna().sum(axis=1)
            consistency = 1 - (col_counts.std() / col_counts.mean()) if col_counts.mean() > 0 else 0
            score += consistency * 0.2
        
        return min(score, 1.0)
    
    def export_tables_to_excel(self, output_path: str, tables: List[ExtractedTable]):
        """Export extracted tables to Excel file."""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for table in tables:
                sheet_name = f"Page_{table.page_number}_{table.table_id}"
                # Truncate sheet name if too long
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]
                
                table.data.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def export_tables_to_csv(self, output_dir: str, tables: List[ExtractedTable]):
        """Export extracted tables to CSV files."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for table in tables:
            filename = f"table_{table.page_number}_{table.table_id}.csv"
            filepath = os.path.join(output_dir, filename)
            table.data.to_csv(filepath, index=False)
    
    def get_table_summary(self, tables: List[ExtractedTable]) -> Dict[str, Any]:
        """Get a summary of extracted tables."""
        summary = {
            'total_tables': len(tables),
            'pages_processed': len(set(t.table_id for t in tables)),
            'tables_by_page': defaultdict(int),
            'average_confidence': 0.0,
            'table_details': []
        }
        
        if tables:
            summary['average_confidence'] = sum(t.confidence_score for t in tables) / len(tables)
            
            for table in tables:
                summary['tables_by_page'][table.page_number] += 1
                summary['table_details'].append({
                    'table_id': table.table_id,
                    'page_number': table.page_number,
                    'rows': len(table.data),
                    'columns': len(table.data.columns),
                    'confidence_score': table.confidence_score,
                    'headers': [h.content for h in table.headers]
                })
        
        return summary 