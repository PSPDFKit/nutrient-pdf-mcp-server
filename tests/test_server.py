"""Tests for MCP server functionality."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pdf_mcp.exceptions import InvalidObjectIDError, PDFParsingError
from pdf_mcp.server import PDFMCPServer


class TestPDFMCPServer:
    """Test the PDF MCP server."""

    @pytest.fixture
    def server(self):
        """Create a server instance."""
        return PDFMCPServer("test-server")

    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF."""
        return Path("res/document.pdf")

    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server.server.name == "test-server"
        assert server.parser is not None

    @pytest.mark.asyncio
    async def test_handle_get_pdf_object_tree_missing_path(self, server):
        """Test get_pdf_object_tree with missing pdf_path."""
        arguments = {}

        with pytest.raises(ValueError, match="pdf_path is required"):
            await server._handle_get_pdf_object_tree(arguments)

    @pytest.mark.asyncio
    async def test_handle_get_pdf_object_tree_nonexistent_file(self, server):
        """Test get_pdf_object_tree with nonexistent file."""
        arguments = {"pdf_path": "nonexistent.pdf"}

        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            await server._handle_get_pdf_object_tree(arguments)

    @pytest.mark.asyncio
    async def test_handle_resolve_indirect_object_missing_params(self, server):
        """Test resolve_indirect_object with missing parameters."""
        # Missing pdf_path
        arguments = {"objnum": 1}
        with pytest.raises(ValueError, match="pdf_path is required"):
            await server._handle_resolve_indirect_object(arguments)

        # Missing objnum
        arguments = {"pdf_path": "test.pdf"}
        with pytest.raises(ValueError, match="objnum is required"):
            await server._handle_resolve_indirect_object(arguments)

    @pytest.mark.asyncio
    async def test_handle_resolve_indirect_object_nonexistent_file(self, server):
        """Test resolve_indirect_object with nonexistent file."""
        arguments = {"pdf_path": "nonexistent.pdf", "objnum": 1, "gennum": 0}

        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            await server._handle_resolve_indirect_object(arguments)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_handle_get_pdf_object_tree_lazy_success(self, server, sample_pdf_path):
        """Test successful get_pdf_object_tree in lazy mode."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        arguments = {"pdf_path": str(sample_pdf_path), "mode": "lazy"}

        result = await server._handle_get_pdf_object_tree(arguments)

        assert len(result) == 1
        assert result[0].type == "text"

        # Parse the JSON response
        response_data = json.loads(result[0].text)
        assert "result" in response_data
        assert isinstance(response_data["result"], dict)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_handle_get_pdf_object_tree_full_success(self, server, sample_pdf_path):
        """Test successful get_pdf_object_tree in full mode."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        arguments = {"pdf_path": str(sample_pdf_path), "mode": "full"}

        result = await server._handle_get_pdf_object_tree(arguments)

        assert len(result) == 1
        assert result[0].type == "text"

        # Parse the JSON response
        response_data = json.loads(result[0].text)
        assert "result" in response_data
        assert "indirect_objects" in response_data
        assert isinstance(response_data["result"], dict)
        assert isinstance(response_data["indirect_objects"], dict)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_handle_resolve_indirect_object_success(self, server, sample_pdf_path):
        """Test successful resolve_indirect_object."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # First get an object ID from lazy parsing
        get_args = {"pdf_path": str(sample_pdf_path), "path": "Pages", "mode": "lazy"}
        get_result = await server._handle_get_pdf_object_tree(get_args)
        get_data = json.loads(get_result[0].text)

        if get_data["result"]["type"] == "indirect_ref":
            objnum = get_data["result"]["objnum"]
            gennum = get_data["result"]["gennum"] or 0

            arguments = {
                "pdf_path": str(sample_pdf_path),
                "objnum": objnum,
                "gennum": gennum,
                "depth": "shallow",
            }

            result = await server._handle_resolve_indirect_object(arguments)

            assert len(result) == 1
            assert result[0].type == "text"

            # Parse the JSON response
            response_data = json.loads(result[0].text)
            assert "object_id" in response_data
            assert "content" in response_data
            assert response_data["object_id"] == f"{objnum}-{gennum}"

    @pytest.mark.asyncio
    async def test_error_handling_pdf_parsing_error(self, server, tmp_path):
        """Test error handling for PDF parsing errors."""
        # Create a temporary file that exists
        temp_file = tmp_path / "test.pdf"
        temp_file.write_text("fake pdf content")

        with patch.object(server.parser, "parse_pdf_lazy") as mock_parse:
            mock_parse.side_effect = PDFParsingError("Test parsing error", "Test details")

            arguments = {"pdf_path": str(temp_file), "mode": "lazy"}

            # The exception should be raised since _handle methods don't catch
            with pytest.raises(PDFParsingError):
                await server._handle_get_pdf_object_tree(arguments)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_object_id(self, server, tmp_path):
        """Test error handling for invalid object ID."""
        # Create a temporary file that exists
        temp_file = tmp_path / "test.pdf"
        temp_file.write_text("fake pdf content")

        with patch.object(server.parser, "resolve_object") as mock_resolve:
            mock_resolve.side_effect = InvalidObjectIDError(
                "Invalid format", "Expected objnum as integer"
            )

            arguments = {"pdf_path": str(temp_file), "objnum": 1, "gennum": 0}

            # The exception should be raised since _handle methods don't catch
            with pytest.raises(InvalidObjectIDError):
                await server._handle_resolve_indirect_object(arguments)

    @pytest.mark.asyncio
    async def test_error_handling_unexpected_error(self, server, tmp_path):
        """Test error handling for unexpected errors."""
        # Create a temporary file that exists
        temp_file = tmp_path / "test.pdf"
        temp_file.write_text("fake pdf content")

        with patch.object(server.parser, "parse_pdf_lazy") as mock_parse:
            mock_parse.side_effect = RuntimeError("Unexpected error")

            arguments = {"pdf_path": str(temp_file), "mode": "lazy"}

            # The exception should be raised since _handle methods don't catch
            with pytest.raises(RuntimeError):
                await server._handle_get_pdf_object_tree(arguments)

    def test_create_server_function(self):
        """Test the create_server factory function."""
        from pdf_mcp.server import create_server

        server = create_server()
        assert isinstance(server, PDFMCPServer)
        assert server.server.name == "nutrient-pdf-mcp"


if __name__ == "__main__":
    pytest.main([__file__])
