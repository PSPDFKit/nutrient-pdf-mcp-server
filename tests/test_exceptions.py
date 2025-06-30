"""Tests for custom exceptions."""

import pytest

from pdf_mcp.exceptions import (
    InvalidObjectIDError,
    InvalidPathError,
    ObjectNotFoundError,
    PDFMCPError,
    PDFParsingError,
)


class TestPDFMCPError:
    """Test base PDFMCPError class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        error = PDFMCPError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None

    def test_exception_with_details(self):
        """Test exception with details."""
        error = PDFMCPError("Test error", "Additional details")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == "Additional details"

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        error = PDFMCPError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, PDFMCPError)


class TestPDFParsingError:
    """Test PDFParsingError class."""

    def test_pdf_parsing_error(self):
        """Test PDF parsing error creation."""
        error = PDFParsingError("Failed to parse PDF")
        assert str(error) == "Failed to parse PDF"
        assert error.message == "Failed to parse PDF"
        assert isinstance(error, PDFMCPError)

    def test_pdf_parsing_error_with_details(self):
        """Test PDF parsing error with details."""
        error = PDFParsingError("Failed to parse PDF", "File is corrupted")
        assert error.details == "File is corrupted"

    def test_raising_pdf_parsing_error(self):
        """Test raising PDF parsing error."""
        with pytest.raises(PDFParsingError) as exc_info:
            raise PDFParsingError("Test parsing error")

        assert "Test parsing error" in str(exc_info.value)


class TestObjectNotFoundError:
    """Test ObjectNotFoundError class."""

    def test_object_not_found_error(self):
        """Test object not found error creation."""
        error = ObjectNotFoundError("Object 1-0 not found")
        assert str(error) == "Object 1-0 not found"
        assert isinstance(error, PDFMCPError)

    def test_object_not_found_error_with_details(self):
        """Test object not found error with details."""
        error = ObjectNotFoundError("Object 1-0 not found", "PDF may be corrupted")
        assert error.details == "PDF may be corrupted"

    def test_raising_object_not_found_error(self):
        """Test raising object not found error."""
        with pytest.raises(ObjectNotFoundError) as exc_info:
            raise ObjectNotFoundError("Object 99-0 not found")

        assert "Object 99-0 not found" in str(exc_info.value)


class TestInvalidPathError:
    """Test InvalidPathError class."""

    def test_invalid_path_error(self):
        """Test invalid path error creation."""
        error = InvalidPathError("Invalid path: Pages.NonExistent")
        assert str(error) == "Invalid path: Pages.NonExistent"
        assert isinstance(error, PDFMCPError)

    def test_invalid_path_error_with_details(self):
        """Test invalid path error with details."""
        error = InvalidPathError(
            "Invalid path step", "Available keys: ['/Type', '/Kids', '/Count']"
        )
        assert error.details == "Available keys: ['/Type', '/Kids', '/Count']"

    def test_raising_invalid_path_error(self):
        """Test raising invalid path error."""
        with pytest.raises(InvalidPathError) as exc_info:
            raise InvalidPathError("Path navigation failed")

        assert "Path navigation failed" in str(exc_info.value)


class TestInvalidObjectIDError:
    """Test InvalidObjectIDError class."""

    def test_invalid_object_id_error(self):
        """Test invalid object ID error creation."""
        error = InvalidObjectIDError("Invalid object ID format")
        assert str(error) == "Invalid object ID format"
        assert isinstance(error, PDFMCPError)

    def test_invalid_object_id_error_with_details(self):
        """Test invalid object ID error with details."""
        error = InvalidObjectIDError("Invalid format", "Expected format: '1-0'")
        assert error.details == "Expected format: '1-0'"

    def test_raising_invalid_object_id_error(self):
        """Test raising invalid object ID error."""
        with pytest.raises(InvalidObjectIDError) as exc_info:
            raise InvalidObjectIDError("Bad object ID")

        assert "Bad object ID" in str(exc_info.value)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_inherit_from_base(self):
        """Test all custom exceptions inherit from PDFMCPError."""
        exceptions = [
            PDFParsingError("test"),
            ObjectNotFoundError("test"),
            InvalidPathError("test"),
            InvalidObjectIDError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, PDFMCPError)
            assert isinstance(exc, Exception)

    def test_exception_catching(self):
        """Test catching exceptions with base class."""

        def raise_parsing_error():
            raise PDFParsingError("Parse failed")

        def raise_object_not_found():
            raise ObjectNotFoundError("Object missing")

        # Should be able to catch all with base class
        with pytest.raises(PDFMCPError):
            raise_parsing_error()

        with pytest.raises(PDFMCPError):
            raise_object_not_found()

    def test_specific_exception_catching(self):
        """Test catching specific exception types."""

        def raise_specific_errors():
            yield PDFParsingError("Parse error")
            yield ObjectNotFoundError("Object error")
            yield InvalidPathError("Path error")
            yield InvalidObjectIDError("ID error")

        for error in raise_specific_errors():
            with pytest.raises(type(error)):
                raise error


if __name__ == "__main__":
    pytest.main([__file__])
