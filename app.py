import streamlit as st
from io import BytesIO
import pandas as pd
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTRect, LTLine, LTFigure
import tempfile
import os
import base64
import re

st.set_page_config(page_title="Advanced PDF Table Extractor", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp { max-width: 1200px; padding: 2rem; }
    .stFileUploader { width: 100%; }
    .stButton>button { background-color: #4CAF50; color: white; }
    .stButton>button:hover { background-color: #45a049; }
    .stDownloadButton>button { background-color: #2196F3; color: white; }
    .stDownloadButton>button:hover { background-color: #0b7dda; }
    .table-preview { max-height: 400px; overflow-y: auto; margin-bottom: 20px; }
    .bold-columns { font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

class AdvancedPDFTableExtractor:
    def __init__(self):
        self.all_tables = {
            'regular_tables': [],
            'tab_separated': [],
            'colon_separated': [],
            'other_delimited': []
        }
        self.min_row_gap = 5
        self.min_col_gap = 5

    def extract_all_tables(self, pdf_path: str):
        """Extract all types of tables from PDF"""
        for page_layout in extract_pages(pdf_path):
            page_elements = []
            for element in page_layout:
                if isinstance(element, (LTTextContainer, LTRect, LTLine, LTFigure)):
                    page_elements.append(element)
            
            self._process_page_elements(page_elements)
        
        return self.all_tables

    def _process_page_elements(self, elements: list):
        """Identify and classify different table types"""
        text_elements = [e for e in elements if isinstance(e, LTTextContainer)]
        
        # First extract regular tables
        self._extract_regular_tables(elements)
        
        # Then look for delimited tables in remaining text
        self._extract_delimited_tables(text_elements)

    def _extract_regular_tables(self, elements: list):
        """Extract tables with visible structure"""
        # Group elements by y-coordinate (rows)
        rows = {}
        for element in elements:
            if isinstance(element, LTTextContainer):
                y = round(element.y0)
                if y not in rows:
                    rows[y] = []
                rows[y].append(element)
        
        # Sort rows top to bottom
        sorted_rows = sorted(rows.items(), key=lambda x: -x[0])
        
        # Create tables from row groups
        table_data = []
        for y, row_elements in sorted_rows:
            row_elements.sort(key=lambda e: e.x0)
            row_data = [e.get_text().strip() for e in row_elements]
            table_data.append(row_data)
        
        if len(table_data) > 1:  # At least header + one row
            df = self._create_dataframe(table_data)
            self.all_tables['regular_tables'].append(df)

    def _extract_delimited_tables(self, elements: list):
        """Extract tables with various delimiters"""
        # Group text into potential table blocks
        text_blocks = self._group_text_blocks(elements)
        
        for block in text_blocks:
            lines = block.split('\n')
            
            # Check for tab-separated
            if any('\t' in line for line in lines):
                self._process_delimited_table(lines, '\t', 'tab_separated')
            
            # Check for colon-separated
            elif any(':' in line and line.count(':') > 1 for line in lines):
                self._process_delimited_table(lines, ':', 'colon_separated')
            
            # Check for other delimiters (|, ;, etc.)
            else:
                for delim in ['|', ';', ',']:
                    if any(delim in line and line.count(delim) > 1 for line in lines):
                        self._process_delimited_table(lines, delim, 'other_delimited')
                        break

    def _process_delimited_table(self, lines: list, delimiter: str, table_type: str):
        """Process a delimited table and add to the appropriate category"""
        table_data = []
        for line in lines:
            if delimiter in line:
                # Clean and split the line
                cleaned = re.sub(r'\s+', ' ', line.strip())  # Normalize whitespace
                row = [cell.strip() for cell in cleaned.split(delimiter)]
                table_data.append(row)
        
        if len(table_data) > 1:  # At least header + one row
            df = self._create_dataframe(table_data)
            self.all_tables[table_type].append(df)

    def _group_text_blocks(self, elements: list) -> list:
        """Group text elements into logical blocks that might be tables"""
        # Sort elements top to bottom, left to right
        sorted_elements = sorted(elements, key=lambda e: (-e.y1, e.x0))
        
        blocks = []
        current_block = []
        prev_y = None
        
        for element in sorted_elements:
            if prev_y is None or abs(prev_y - element.y1) > self.min_row_gap:
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
            current_block.append(element.get_text())
            prev_y = element.y1
        
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks

    def _create_dataframe(self, table_data: list) -> pd.DataFrame:
        """Create DataFrame from table data with proper headers"""
        headers = table_data[0]
        rows = table_data[1:]
        
        # Ensure all rows have same number of columns as headers
        max_cols = len(headers)
        cleaned_rows = []
        for row in rows:
            if len(row) > max_cols:
                row = row[:max_cols]  # Truncate extra columns
            elif len(row) < max_cols:
                row += [''] * (max_cols - len(row))  # Pad missing columns
            cleaned_rows.append(row)
        
        return pd.DataFrame(cleaned_rows, columns=headers)

def create_excel_download(all_tables: dict, filename: str) -> str:
    """Create Excel file with separate sheets for each table type"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Regular tables
        for i, table in enumerate(all_tables['regular_tables'], 1):
            table.to_excel(writer, sheet_name=f'Regular Table {i}', index=False)
        
        # Tab-separated tables
        for i, table in enumerate(all_tables['tab_separated'], 1):
            table.to_excel(writer, sheet_name=f'Tab Table {i}', index=False)
        
        # Colon-separated tables
        for i, table in enumerate(all_tables['colon_separated'], 1):
            table.to_excel(writer, sheet_name=f'Colon Table {i}', index=False)
        
        # Other delimited tables
        for i, table in enumerate(all_tables['other_delimited'], 1):
            table.to_excel(writer, sheet_name=f'Delimited Table {i}', index=False)
    
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download All Tables (Excel)</a>'

def main():
    st.title("Advanced PDF Table Extractor")
    st.markdown("Upload a PDF to extract all types of tables (regular, tab-separated, colon-separated, etc.)")
    
    uploaded_file = st.file_uploader("Choose PDF file", type="pdf")
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            extractor = AdvancedPDFTableExtractor()
            all_tables = extractor.extract_all_tables(tmp_path)
            
            # Display summary
            st.success(f"""
            Extracted:
            - {len(all_tables['regular_tables'])} regular tables
            - {len(all_tables['tab_separated'])} tab-separated tables
            - {len(all_tables['colon_separated'])} colon-separated tables
            - {len(all_tables['other_delimited'])} other delimited tables
            """)
            
            # Download button for all tables
            st.markdown(create_excel_download(
                all_tables,
                f"{os.path.splitext(uploaded_file.name)[0]}_all_tables.xlsx"
            ), unsafe_allow_html=True)
            
            # Show previews
            st.markdown("## Table Previews")
            
            # Regular tables
            if all_tables['regular_tables']:
                st.markdown("### Regular Tables")
                for i, table in enumerate(all_tables['regular_tables'], 1):
                    with st.expander(f"Regular Table {i} ({table.shape[1]} columns × {table.shape[0]} rows)"):
                        st.dataframe(table.head())
            
            # Tab-separated tables
            if all_tables['tab_separated']:
                st.markdown("### Tab-Separated Tables")
                for i, table in enumerate(all_tables['tab_separated'], 1):
                    with st.expander(f"Tab-Separated Table {i} ({table.shape[1]} columns × {table.shape[0]} rows)"):
                        st.dataframe(table.head())
            
            # Colon-separated tables
            if all_tables['colon_separated']:
                st.markdown("### Colon-Separated Tables")
                for i, table in enumerate(all_tables['colon_separated'], 1):
                    with st.expander(f"Colon-Separated Table {i} ({table.shape[1]} columns × {table.shape[0]} rows)"):
                        st.dataframe(table.head())
            
            # Other delimited tables
            if all_tables['other_delimited']:
                st.markdown("### Other Delimited Tables")
                for i, table in enumerate(all_tables['other_delimited'], 1):
                    with st.expander(f"Delimited Table {i} ({table.shape[1]} columns × {table.shape[0]} rows)"):
                        st.dataframe(table.head())
        
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

if __name__ == "__main__":
    main()