"""Nutrient PDF MCP Server - Advanced PDF object tree investigation with lazy loading support."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities

from .exceptions import PDFMCPError
from .parser import PDFObjectTreeParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFMCPServer:
    """Nutrient PDF MCP Server - Advanced PDF object tree investigation.

    Provides tools for:
    - Lazy loading of PDF object trees
    - Selective resolution of indirect objects
    - Path-based navigation through PDF structure
    """

    def __init__(self, name: str = "nutrient-pdf-mcp") -> None:
        self.server: Server = Server(name)
        self.parser = PDFObjectTreeParser()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self.server.list_tools()  # type: ignore[misc]
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="get_pdf_object_tree",
                    description="Nutrient PDF MCP Server - Get JSON representation of PDF object tree with lazy loading",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string", "description": "Path to the PDF file"},
                            "object_id": {
                                "type": "string",
                                "description": "Optional: specific object ID to retrieve (e.g., '1 0')",
                            },
                            "path": {
                                "type": "string",
                                "description": "Optional: object path to navigate (e.g., 'Pages.Kids.0')",
                            },
                            "mode": {
                                "type": "string",
                                "description": "Parsing mode: 'lazy' (default) or 'full'",
                                "enum": ["lazy", "full"],
                                "default": "lazy",
                            },
                        },
                        "required": ["pdf_path"],
                    },
                ),
                types.Tool(
                    name="resolve_indirect_object",
                    description="Nutrient PDF MCP Server - Resolve a specific indirect object by its ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {"type": "string", "description": "Path to the PDF file"},
                            "object_id": {
                                "type": "string",
                                "description": "Indirect object ID to resolve (e.g., '1-0')",
                            },
                            "depth": {
                                "type": "string",
                                "description": "Resolution depth: 'shallow' (default, only direct properties) or 'deep' (resolve all nested objects)",
                                "enum": ["shallow", "deep"],
                                "default": "shallow",
                            },
                        },
                        "required": ["pdf_path", "object_id"],
                    },
                ),
            ]

        @self.server.call_tool()  # type: ignore[misc]
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_pdf_object_tree":
                    return await self._handle_get_pdf_object_tree(arguments)
                elif name == "resolve_indirect_object":
                    return await self._handle_resolve_indirect_object(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except PDFMCPError as e:
                logger.error(f"PDF MCP error in {name}: {e.message}")
                error_response = {"error": e.message, "details": e.details, "tool": name}
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            except Exception as e:
                logger.error(f"Unexpected error in {name}: {e}")
                error_response = {"error": f"Internal server error: {str(e)}", "tool": name}
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def _handle_get_pdf_object_tree(
        self, arguments: dict[str, Any]
    ) -> list[types.TextContent]:
        """Handle get_pdf_object_tree tool calls."""
        pdf_path = arguments.get("pdf_path")
        object_id = arguments.get("object_id")
        path_arg = arguments.get("path")
        mode = arguments.get("mode", "lazy")

        if not pdf_path:
            raise ValueError("pdf_path is required")

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Parsing PDF {pdf_path} in {mode} mode")

        if mode == "lazy":
            result = self.parser.parse_pdf_lazy(str(path), object_id, path_arg)
        else:
            result = self.parser.parse_pdf_full(str(path), object_id, path_arg)

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_resolve_indirect_object(
        self, arguments: dict[str, Any]
    ) -> list[types.TextContent]:
        """Handle resolve_indirect_object tool calls."""
        pdf_path = arguments.get("pdf_path")
        object_id = arguments.get("object_id")
        depth = arguments.get("depth", "shallow")

        if not pdf_path:
            raise ValueError("pdf_path is required")
        if not object_id:
            raise ValueError("object_id is required")

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Resolving object {object_id} from {pdf_path} with {depth} depth")

        result = self.parser.resolve_object(str(path), object_id, depth)

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting PDF MCP server")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="nutrient-pdf-mcp",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(),
                ),
            )


def create_server() -> PDFMCPServer:
    """Create and return a Nutrient PDF MCP server instance."""
    return PDFMCPServer()


async def main() -> None:
    """Main entry point for the Nutrient PDF MCP Server."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
