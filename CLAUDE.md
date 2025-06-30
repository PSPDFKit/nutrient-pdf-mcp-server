# Nutrient PDF MCP Server - Claude Memory

## Project Overview
This is the Nutrient PDF MCP Server, a Model Context Protocol (MCP) server for investigating PDF object trees with lazy loading support. The server allows LLMs to explore PDF structure efficiently by providing selective resolution of indirect objects and path-based navigation.

## Key Features
- **Lazy Loading**: Only resolves indirect objects on demand to reduce token usage
- **Path Navigation**: Supports dot notation paths like `Pages.Kids.0` for drilling down
- **Two Resolution Modes**: Shallow (single object) and deep (with dependencies)
- **Type Safety**: Comprehensive TypedDict definitions for all PDF objects
- **Error Handling**: Custom exception hierarchy with detailed error messages

## Architecture
- `pdf_mcp/server.py` - Main MCP server with two tools
- `pdf_mcp/parser.py` - Core PDF parsing logic with pypdf integration
- `pdf_mcp/types.py` - Type definitions for PDF objects and responses
- `pdf_mcp/exceptions.py` - Custom exception hierarchy

## MCP Tools
1. **get_pdf_object_tree** - Get JSON representation of PDF structure
   - Parameters: pdf_path, mode (lazy/full), path (optional), object_id (optional)
2. **resolve_indirect_object** - Resolve specific indirect objects by ID
   - Parameters: pdf_path, object_id, depth (shallow/deep)

## Development
- Python 3.10+ required (for MCP library pattern matching)
- Use `make` commands for common tasks:
  - `make test` - Run test suite (64 tests)
  - `make test-cov` - Run tests with coverage analysis
  - `make quality` - Run all quality checks (format, lint, type check, test)
  - `make format` - Auto-format code with black/isort
  - `make lint` - Check code with ruff
  - `make typecheck` - Type check with mypy

## Quality Standards
- 76% test coverage with comprehensive test suite
- Full type checking with mypy (custom overrides for pypdf interactions)
- Modern Python syntax (union types with |, lowercase builtins)
- Code formatting with black, isort, ruff

## Usage Examples
```bash
# Start Nutrient PDF MCP Server for Claude Code
./run-pdf-mcp.sh

# Manual testing
python -m pdf_mcp.server

# Using the installed command
nutrient-pdf-mcp
```

## Token Efficiency
Lazy loading reduces response sizes from 500+ lines to ~50 lines for shallow exploration, making it practical for LLM usage while maintaining full PDF investigation capabilities.