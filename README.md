# pdfParser
Streamlit
Python
A Streamlit application that extracts tables from PDF documents, handling various formats including bordered tables, borderless tables, tab-separated values, and colon-separated values.

Features ✨
Multi-format extraction: Handles different table formats in PDFs

Bordered tables: Extracts tables with visible borders

Borderless tables: Identifies tables without visible borders

Delimited content: Extracts tab-separated and colon-separated values

Preview functionality: View extracted tables before downloading

Export options: Download tables as CSV or in a ZIP archive

Robust processing: Handles non-ASCII characters and complex layouts

Installation 🛠️
Clone the repository:

bash
Copy
git clone https://github.com/kk235964/pdfParser.git
cd hack36
Create and activate a virtual environment (recommended):

bash
Copy
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install the required packages:

bash
Copy
pip install -r requirements.txt
Usage 🚀
Run the Streamlit application:

bash
Copy
streamlit run pdf_table_extractor.py
Upload a PDF file through the web interface

View the extracted tables in the preview section

Download the tables:

Individual tables as CSV files

All tables together in a ZIP archive

Requirements 📋
Python 3.7+

Streamlit

pdfplumber

pandas

Additional dependencies listed in requirements.txt

How It Works 🔍
The application uses multiple strategies to extract tables from PDFs:

Bordered tables: Identified by visible lines using pdfplumber's line detection

Borderless tables: Detected through text alignment patterns

Tab-separated values: Extracted using tab characters as delimiters

Colon-separated values: Parsed from key:value patterns

Sample video 📸
[Drive Link](https://drive.google.com/file/d/1m6CRuf_69agDUK07c5eG6TF3dJWj_pEy/view?usp=sharing)
Main interface with table previews
