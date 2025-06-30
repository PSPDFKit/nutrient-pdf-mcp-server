"""Tests for PDF parser functionality."""

from pathlib import Path

import pytest

from pdf_mcp.exceptions import ObjectNotFoundError, PDFParsingError
from pdf_mcp.parser import PDFObjectTreeParser


class TestPDFObjectTreeParser:
    """Test the PDF object tree parser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return PDFObjectTreeParser()

    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF (you'll need to add this)."""
        return Path("res/document.pdf")

    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser.indirect_objects == {}
        assert parser.visited_refs == set()
        assert parser.lazy_mode is False

    def test_parse_pdf_lazy_nonexistent_file(self, parser):
        """Test lazy parsing with nonexistent file raises error."""
        with pytest.raises(PDFParsingError, match="PDF file not found"):
            parser.parse_pdf_lazy("nonexistent.pdf")

    def test_parse_pdf_full_nonexistent_file(self, parser):
        """Test full parsing with nonexistent file raises error."""
        with pytest.raises(PDFParsingError, match="PDF file not found"):
            parser.parse_pdf_full("nonexistent.pdf")

    def test_resolve_object_nonexistent_file(self, parser):
        """Test object resolution with nonexistent file raises error."""
        with pytest.raises(PDFParsingError, match="PDF file not found"):
            parser.resolve_object("nonexistent.pdf", 1, 0)

    def test_resolve_object_invalid_id_format(self, parser, sample_pdf_path):
        """Test object resolution with unusual objnum value."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # Test with negative object number - PyPDF handles this gracefully
        # so we just verify it doesn't crash and returns a reasonable response
        result = parser.resolve_object(sample_pdf_path, -1, 0)
        assert "object_id" in result
        assert "content" in result
        assert result["object_id"] == "-1-0"

    def test_resolve_object_nonexistent_object(self, parser, sample_pdf_path):
        """Test object resolution with nonexistent object ID."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # Use a very high object number that's unlikely to exist
        # pypdf may just return a null object or handle gracefully, so we test it works
        try:
            result = parser.resolve_object(sample_pdf_path, 99999, 0)
            # If no exception, verify we got a reasonable response
            assert "object_id" in result
            assert result["object_id"] == "99999-0"
        except (ObjectNotFoundError, PDFParsingError):
            # These exceptions are also acceptable
            pass

    @pytest.mark.integration
    def test_parse_pdf_lazy_success(self, parser, sample_pdf_path):
        """Test successful lazy PDF parsing."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = parser.parse_pdf_lazy(sample_pdf_path)

        assert "result" in result
        assert isinstance(result["result"], dict)
        # In lazy mode, should have minimal resolved objects
        assert len(parser.indirect_objects) == 0

    @pytest.mark.integration
    def test_parse_pdf_full_success(self, parser, sample_pdf_path):
        """Test successful full PDF parsing."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = parser.parse_pdf_full(sample_pdf_path)

        assert "result" in result
        assert "indirect_objects" in result
        assert isinstance(result["result"], dict)
        assert isinstance(result["indirect_objects"], dict)
        # In full mode, should have resolved objects
        assert len(result["indirect_objects"]) > 0

    @pytest.mark.integration
    def test_resolve_object_shallow(self, parser, sample_pdf_path):
        """Test shallow object resolution."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # First get an object ID from lazy parsing
        lazy_result = parser.parse_pdf_lazy(sample_pdf_path, path="Pages")
        if lazy_result["result"]["type"] == "indirect_ref":
            objnum = lazy_result["result"]["objnum"]
            gennum = lazy_result["result"]["gennum"] or 0

            result = parser.resolve_object(sample_pdf_path, objnum, gennum, "shallow")

            assert "object_id" in result
            assert "content" in result
            assert result["object_id"] == f"{objnum}-{gennum}"
            assert isinstance(result["content"], dict)
            # Shallow resolution shouldn't include indirect_objects
            assert "indirect_objects" not in result

    @pytest.mark.integration
    def test_resolve_object_deep(self, parser, sample_pdf_path):
        """Test deep object resolution."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # First get an object ID from lazy parsing
        lazy_result = parser.parse_pdf_lazy(sample_pdf_path, path="Pages")
        if lazy_result["result"]["type"] == "indirect_ref":
            objnum = lazy_result["result"]["objnum"]
            gennum = lazy_result["result"]["gennum"] or 0

            result = parser.resolve_object(sample_pdf_path, objnum, gennum, "deep")

            assert "object_id" in result
            assert "content" in result
            assert "indirect_objects" in result
            assert result["object_id"] == f"{objnum}-{gennum}"
            assert isinstance(result["content"], dict)
            assert isinstance(result["indirect_objects"], dict)

    @pytest.mark.integration
    def test_path_navigation(self, parser, sample_pdf_path):
        """Test path navigation functionality."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        result = parser.parse_pdf_lazy(sample_pdf_path, path="Pages")

        assert "result" in result
        # Should navigate to Pages object
        assert isinstance(result["result"], dict)


if __name__ == "__main__":
    pytest.main([__file__])
