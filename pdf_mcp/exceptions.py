"""Custom exceptions for the PDF MCP server."""


class PDFMCPError(Exception):
    """Base exception for PDF MCP operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class PDFParsingError(PDFMCPError):
    """Raised when PDF parsing fails."""

    pass


class ObjectNotFoundError(PDFMCPError):
    """Raised when a requested PDF object is not found."""

    pass


class InvalidPathError(PDFMCPError):
    """Raised when path navigation fails."""

    pass


class InvalidObjectIDError(PDFMCPError):
    """Raised when an object ID has invalid format."""

    pass
