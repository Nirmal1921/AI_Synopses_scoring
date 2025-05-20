import PyPDF2
import io
import os

def read_txt_file(file_path):
    """Read content from a text file"""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def read_pdf_file(file_path):
    """Extract text from a PDF file"""
    with open(file_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:  # Some pages might be empty
                text += page_text + "\n"
        return text

def extract_text_from_file(file_path):
    """Extract text from a file (PDF or TXT)"""
    if file_path.lower().endswith('.pdf'):
        return read_pdf_file(file_path)
    else:  # Assume it's a text file
        return read_txt_file(file_path)

def save_uploaded_file(uploaded_file):
    """Save an uploaded file to a temporary location and return the path"""
    if uploaded_file is None:
        return None
        
    # Create a temporary file to store the uploaded content
    file_extension = os.path.splitext(uploaded_file.name)[1]
    temp_file = f"temp_{uploaded_file.name}"
    
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return temp_file