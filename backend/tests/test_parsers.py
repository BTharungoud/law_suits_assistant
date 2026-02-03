"""
Unit tests for file parsers.
"""

import pytest
from app.utils.parsers import parse_text, extract_text_from_file


class TestParsers:
    """Tests for file parsing utilities."""
    
    def test_parse_text_simple(self):
        """Test parsing simple text."""
        text = "This is a test case document."
        file_bytes = text.encode('utf-8')
        result = parse_text(file_bytes)
        assert result == text
    
    def test_parse_text_multiline(self):
        """Test parsing multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        file_bytes = text.encode('utf-8')
        result = parse_text(file_bytes)
        assert result == text
    
    def test_parse_text_with_whitespace(self):
        """Test parsing text with leading/trailing whitespace."""
        text = "  Content with spaces  "
        file_bytes = text.encode('utf-8')
        result = parse_text(file_bytes)
        assert result == "Content with spaces"
    
    def test_extract_text_from_file_txt(self):
        """Test extracting text from TXT file."""
        text = "Test case content"
        file_bytes = text.encode('utf-8')
        result = extract_text_from_file(file_bytes, "test.txt")
        assert result == text
    
    def test_extract_text_from_file_unsupported(self):
        """Test that unsupported file types raise error."""
        file_bytes = b"content"
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text_from_file(file_bytes, "test.doc")
    
    def test_parse_text_empty(self):
        """Test parsing empty text."""
        file_bytes = b""
        result = parse_text(file_bytes)
        assert result == ""
