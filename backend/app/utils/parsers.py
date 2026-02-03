"""
File parsers for extracting text from PDF, DOCX, and plain text files.
"""

import io
from typing import Optional


def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_bytes: PDF file contents as bytes
        
    Returns:
        Extracted text from PDF
    """
    try:
        import PyPDF2
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def parse_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX file.
    
    Args:
        file_bytes: DOCX file contents as bytes
        
    Returns:
        Extracted text from DOCX
    """
    try:
        from docx import Document
        
        doc = Document(io.BytesIO(file_bytes))
        text = ""
        
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {str(e)}")


def parse_text(file_bytes: bytes) -> str:
    """
    Extract text from plain text file.
    
    Args:
        file_bytes: Text file contents as bytes
        
    Returns:
        Extracted text
    """
    try:
        text = file_bytes.decode("utf-8")
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse text file: {str(e)}")


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Route file parsing based on file extension.
    
    Args:
        file_bytes: File contents as bytes
        filename: Original filename (for extension detection)
        
    Returns:
        Extracted text
        
    Raises:
        ValueError: If file type is unsupported
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif filename_lower.endswith(".docx"):
        return parse_docx(file_bytes)
    elif filename_lower.endswith(".txt"):
        return parse_text(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Supported: PDF, DOCX, TXT")
