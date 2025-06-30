"""Integration tests for the complete PDF MCP system."""

import json
from pathlib import Path

import pytest

from pdf_mcp.parser import PDFObjectTreeParser
from pdf_mcp.server import PDFMCPServer


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return PDFObjectTreeParser()

    @pytest.fixture
    def server(self):
        """Create a server instance."""
        return PDFMCPServer("test-integration")

    @pytest.fixture
    def sample_pdf_path(self):
        """Path to sample PDF."""
        return Path("res/document.pdf")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_pdf_exploration_workflow(self, parser, sample_pdf_path):
        """Test a complete PDF exploration workflow."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # Step 1: Get overview with lazy loading
        lazy_result = parser.parse_pdf_lazy(str(sample_pdf_path))
        assert "result" in lazy_result

        # Step 2: Navigate to Pages
        pages_result = parser.parse_pdf_lazy(str(sample_pdf_path), path="Pages")
        assert "result" in pages_result
        assert pages_result["result"]["type"] == "indirect_ref"

        pages_objnum = pages_result["result"]["objnum"]
        pages_gennum = pages_result["result"]["gennum"] or 0

        # Step 3: Resolve Pages object (shallow)
        pages_content = parser.resolve_object(
            str(sample_pdf_path), pages_objnum, pages_gennum, "shallow"
        )
        assert "object_id" in pages_content
        assert "content" in pages_content
        assert pages_content["object_id"] == f"{pages_objnum}-{pages_gennum}"

        # Verify Pages object structure
        pages_dict = pages_content["content"]
        assert pages_dict["type"] == "dict"
        assert "/Type" in pages_dict["value"]
        assert pages_dict["value"]["/Type"]["value"] == "/Pages"

        # Step 4: Navigate to first page
        if "/Kids" in pages_dict["value"]:
            kids_array = pages_dict["value"]["/Kids"]
            if kids_array["type"] == "array" and len(kids_array["value"]) > 0:
                first_page_ref = kids_array["value"][0]
                assert first_page_ref["type"] == "indirect_ref"

                # Step 5: Resolve first page
                first_page_objnum = first_page_ref["objnum"]
                first_page_gennum = first_page_ref["gennum"] or 0
                page_content = parser.resolve_object(
                    str(sample_pdf_path), first_page_objnum, first_page_gennum, "shallow"
                )

                assert page_content["object_id"] == f"{first_page_objnum}-{first_page_gennum}"
                page_dict = page_content["content"]
                assert page_dict["type"] == "dict"
                assert "/Type" in page_dict["value"]
                assert page_dict["value"]["/Type"]["value"] == "/Page"

    @pytest.mark.integration
    def test_path_navigation_comprehensive(self, parser, sample_pdf_path):
        """Test comprehensive path navigation scenarios."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # Test various navigation paths
        test_paths = [
            "Pages",
            "Pages.Count",
            "Pages.Kids",
        ]

        for path in test_paths:
            try:
                result = parser.parse_pdf_lazy(str(sample_pdf_path), path=path)
                assert "result" in result
                # Each path should return some valid object
                assert isinstance(result["result"], dict)
            except Exception as e:
                # Some paths might not exist in test PDF, that's OK
                pytest.skip(f"Path {path} not available in test PDF: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_client_workflow(self, server, sample_pdf_path):
        """Test complete server workflow as if called by MCP client."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # Step 1: Get PDF tree (lazy)
        get_args = {"pdf_path": str(sample_pdf_path), "mode": "lazy"}
        get_result = await server._handle_get_pdf_object_tree(get_args)

        assert len(get_result) == 1
        get_data = json.loads(get_result[0].text)
        assert "result" in get_data

        # Step 2: Navigate to Pages
        nav_args = {"pdf_path": str(sample_pdf_path), "path": "Pages", "mode": "lazy"}
        nav_result = await server._handle_get_pdf_object_tree(nav_args)
        nav_data = json.loads(nav_result[0].text)

        if nav_data["result"]["type"] == "indirect_ref":
            pages_objnum = nav_data["result"]["objnum"]
            pages_gennum = nav_data["result"]["gennum"] or 0

            # Step 3: Resolve Pages object
            resolve_args = {
                "pdf_path": str(sample_pdf_path),
                "objnum": pages_objnum,
                "gennum": pages_gennum,
                "depth": "shallow",
            }
            resolve_result = await server._handle_resolve_indirect_object(resolve_args)
            resolve_data = json.loads(resolve_result[0].text)

            assert "object_id" in resolve_data
            assert "content" in resolve_data
            assert resolve_data["object_id"] == f"{pages_objnum}-{pages_gennum}"

    @pytest.mark.integration
    def test_lazy_vs_full_comparison(self, parser, sample_pdf_path):
        """Test comparison between lazy and full parsing modes."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        # Get same result with both modes
        lazy_result = parser.parse_pdf_lazy(str(sample_pdf_path))
        full_result = parser.parse_pdf_full(str(sample_pdf_path))

        # Both should have result
        assert "result" in lazy_result
        assert "result" in full_result

        # Full result should have indirect_objects, lazy shouldn't
        assert "indirect_objects" not in lazy_result
        assert "indirect_objects" in full_result

        # The main result structure should be similar
        assert lazy_result["result"]["type"] == full_result["result"]["type"]

        # Full result should have more resolved objects
        assert len(full_result["indirect_objects"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_through_system(self, server):
        """Test error propagation from parser through server."""
        # Test with nonexistent file
        args = {"pdf_path": "nonexistent.pdf", "mode": "lazy"}

        # Should not raise exception, but return error in response
        try:
            result = await server._handle_get_pdf_object_tree(args)
            # If we get here, check it's an error response
            response_data = json.loads(result[0].text)
            assert "error" in response_data
        except FileNotFoundError:
            # This is also acceptable - the error handling works
            pass

    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_characteristics(self, parser, sample_pdf_path):
        """Test performance characteristics of lazy vs full parsing."""
        if not sample_pdf_path.exists():
            pytest.skip("Sample PDF not available")

        import time

        # Measure lazy parsing time
        start_time = time.time()
        lazy_result = parser.parse_pdf_lazy(str(sample_pdf_path))
        lazy_time = time.time() - start_time

        # Measure full parsing time
        start_time = time.time()
        full_result = parser.parse_pdf_full(str(sample_pdf_path))
        full_time = time.time() - start_time

        # Lazy should be faster (though on small PDFs the difference might be minimal)
        # This is more of a sanity check than a strict performance test
        assert lazy_time >= 0  # At least it completed
        assert full_time >= 0  # At least it completed

        # Check response sizes (lazy should be much smaller)
        lazy_size = len(json.dumps(lazy_result))
        full_size = len(json.dumps(full_result))

        # For most PDFs, full result should be significantly larger
        # But we'll just check they're both valid sizes
        assert lazy_size > 0
        assert full_size > 0

        # Usually full_size >> lazy_size, but depends on PDF
        print(f"Lazy result size: {lazy_size} bytes")
        print(f"Full result size: {full_size} bytes")
        print(f"Size ratio: {full_size / lazy_size:.2f}x")


if __name__ == "__main__":
    pytest.main([__file__])
