# Nutrient PDF MCP Server

> **A powerful Model Context Protocol server for LLM-driven PDF document analysis and exploration**

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for investigating PDF object trees with lazy loading support. This tool allows LLMs to efficiently explore PDF document structure without overwhelming token limits.

## Features

- **Lazy Loading**: Explore PDF structure without loading entire object trees
- **Path Navigation**: Navigate through PDF objects using dot notation (e.g., `Pages.Kids.0`)
- **Selective Resolution**: Resolve specific indirect objects on demand
- **Token Efficient**: Massive reduction in response sizes compared to full tree dumps
- **Type Safe**: Comprehensive type hints and error handling

## Installation

### Optional `asdf` setup

You'll need `python` and `nodejs` installed on your machine. You can optionally use `asdf`.

- [Install and configure `asdf` version manager](https://asdf-vm.com/guide/getting-started.html)
- [Install `asdf` `nodejs` plugin](https://github.com/asdf-vm/asdf-nodejs)
- [Install `asdf` `python` plugin](https://github.com/asdf-community/asdf-python)

Finally install required tools with:

```sh
git clone https://github.com/PSPDFKit/nutrient-pdf-mcp-server.git
cd nutrient-pdf-mcp-server
asdf install

# Install pipx for Python
python -m pip install --user pipx
```

Proceed with the rest of the installation after that.

### Quick Start

```bash
git clone https://github.com/PSPDFKit/nutrient-pdf-mcp-server.git
cd nutrient-pdf-mcp-server
make install-dev  # Sets up development environment
```

### For Claude Code CLI

**Recommended: Build and Install**

```bash
pip install build
make build
pipx install dist/nutrient_pdf_mcp-1.0.0-py3-none-any.whl
claude mcp add nutrient-pdf-mcp nutrient-pdf-mcp
```

If using `asdf`, you might need to configure `pipx` with the following before running:

```sh
export PIPX_DEFAULT_PYTHON=$(asdf which python)
pipx install dist/nutrient_pdf_mcp-1.0.0-py3-none-any.whl
```

**Development Mode**

```bash
make install-dev
claude mcp add nutrient-pdf-mcp "$(pwd)/venv/bin/python" -m pdf_mcp.server
```

#### Manual Configuration

```json
{
  "mcpServers": {
    "nutrient-pdf-mcp": {
      "command": "python",
      "args": ["-m", "pdf_mcp.server"]
    }
  }
}
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

Nutrient PDF MCP Server - Resolve a specific indirect object by its object and generation numbers.

**Parameters:**

- `pdf_path` (required): Path to the PDF file
- `objnum` (required): PDF object number (e.g., 3)
- `gennum` (optional): PDF generation number (defaults to 0)
- `depth` (optional): Resolution depth - 'shallow' (default) or 'deep'

**Examples:**

```json
{
  "pdf_path": "document.pdf",
  "objnum": 3,
  "gennum": 0,
  "depth": "shallow"
}
```

### Command Line Usage

```bash
# Run the server
make serve

# Or run with debug logging
make serve-debug
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
    "/Type": { "type": "name", "value": "/Pages" },
    "/Kids": {
      "type": "array",
      "value": [{ "type": "indirect_ref", "objnum": 2, "gennum": 0 }]
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
3. **Resolve specific page**: `resolve_indirect_object(objnum=3, gennum=0, depth="shallow")`
4. **Deep dive when needed**: `resolve_indirect_object(objnum=3, gennum=0, depth="deep")`

### Path Navigation Examples

- `"Pages"` - Navigate to Pages object
- `"Pages.Kids"` - Get Kids array from Pages
- `"Pages.Kids.0"` - Get first page
- `"Pages.Kids.0.MediaBox.2"` - Get width from MediaBox array

## Development

### Quick Start

```bash
# Set up development environment
make install-dev

# Run all quality checks (format, lint, typecheck, test)
make quality

# Or run individual commands
make test          # Run tests
make format        # Format code
make lint          # Run linter
make typecheck     # Type checking
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
└── README.md
```

## Publishing to PyPI

```bash
# Build the package
make build

# Upload to test PyPI first
twine upload --repository testpypi dist/*

# Upload to production PyPI
twine upload dist/*
```

After publishing, users can install with:

```bash
pipx install nutrient-pdf-mcp
# or
pip install --user nutrient-pdf-mcp
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
