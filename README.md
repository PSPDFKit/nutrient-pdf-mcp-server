# Nutrient PDF MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for investigating PDF object trees with lazy loading support, powered by Nutrient. This tool allows LLMs to efficiently explore PDF document structure without overwhelming token limits.

## Features

- **Lazy Loading**: Explore PDF structure without loading entire object trees
- **Path Navigation**: Navigate through PDF objects using dot notation (e.g., `Pages.Kids.0`)
- **Selective Resolution**: Resolve specific indirect objects on demand
- **Token Efficient**: Massive reduction in response sizes compared to full tree dumps
- **Type Safe**: Comprehensive type hints and error handling

## Installation

### From Source

```bash
git clone https://github.com/PSPDFKit/nutrient-pdf-mcp-server.git
cd nutrient-pdf-mcp-server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### For Development

```bash
pip install -e ".[dev]"
```

## Usage

### As MCP Server

Use with Claude Code or other MCP clients:

```bash
/path/to/nutrient-pdf-mcp-server/run-pdf-mcp.sh
```

### Available Tools

#### `get_pdf_object_tree`

Nutrient PDF MCP Server - Get JSON representation of PDF object tree with lazy loading.

**Parameters:**
- `pdf_path` (required): Path to the PDF file
- `object_id` (optional): Specific object ID to retrieve (e.g., '1 0')
- `path` (optional): Object path to navigate (e.g., 'Pages.Kids.0')
- `mode` (optional): Parsing mode - 'lazy' (default) or 'full'

**Examples:**
```json
{
  "pdf_path": "document.pdf",
  "mode": "lazy"
}
```

```json
{
  "pdf_path": "document.pdf",
  "path": "Pages.Kids.0",
  "mode": "lazy"
}
```

#### `resolve_indirect_object`

Nutrient PDF MCP Server - Resolve a specific indirect object by its ID.

**Parameters:**
- `pdf_path` (required): Path to the PDF file
- `object_id` (required): Indirect object ID to resolve (e.g., '1-0')
- `depth` (optional): Resolution depth - 'shallow' (default) or 'deep'

**Examples:**
```json
{
  "pdf_path": "document.pdf",
  "object_id": "3-0",
  "depth": "shallow"
}
```

### Command Line Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run the Nutrient PDF MCP Server
nutrient-pdf-mcp

# Or run manually
python -m pdf_mcp.server
```

## Architecture

### Core Components

- **`parser.py`**: Main PDF parsing logic with lazy loading support
- **`server.py`**: MCP server implementation
- **`types.py`**: Type definitions for PDF objects and responses
- **`exceptions.py`**: Custom exception classes

### Response Types

All PDF objects are serialized into a consistent JSON format:

```json
{
  "type": "dict",
  "value": {
    "/Type": {"type": "name", "value": "/Pages"},
    "/Kids": {
      "type": "array", 
      "value": [
        {"type": "indirect_ref", "id": "2-0"}
      ]
    }
  }
}
```

### Token Efficiency

The lazy loading system provides massive token savings:

- **Lazy mode**: ~5-50 lines (minimal tokens)
- **Shallow resolution**: ~50-100 lines (reasonable tokens)  
- **Deep resolution**: 500+ lines (use sparingly)

## Examples

### Exploring PDF Structure

1. **Get overview**: `get_pdf_object_tree(path="document.pdf", mode="lazy")`
2. **Navigate to pages**: `get_pdf_object_tree(path="document.pdf", path="Pages", mode="lazy")`
3. **Resolve specific page**: `resolve_indirect_object(object_id="3-0", depth="shallow")`
4. **Deep dive when needed**: `resolve_indirect_object(object_id="3-0", depth="deep")`

### Path Navigation Examples

- `"Pages"` - Navigate to Pages object
- `"Pages.Kids"` - Get Kids array from Pages
- `"Pages.Kids.0"` - Get first page
- `"Pages.Kids.0.MediaBox.2"` - Get width from MediaBox array

## Development

### Code Quality

```bash
# Format code
black .
isort .

# Type checking
mypy pdf_mcp/

# Linting
ruff check .

# Run tests
pytest
```

### Project Structure

```
nutrient-pdf-mcp-server/
├── pdf_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP server
│   ├── parser.py          # PDF parsing logic
│   ├── types.py           # Type definitions
│   └── exceptions.py      # Custom exceptions
├── tests/                 # Test suite
├── res/                   # Sample PDFs
├── pyproject.toml         # Project configuration
├── README.md
└── run-pdf-mcp.sh        # Launch script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure code quality checks pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io)
- [PyPDF](https://pypdf.readthedocs.io/)
- [Claude Code](https://claude.ai/code)