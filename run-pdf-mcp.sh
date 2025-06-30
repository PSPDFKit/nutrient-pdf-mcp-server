#!/bin/bash

# Nutrient PDF MCP Server - Claude Code compatible launcher
# Usage: ./run-pdf-mcp.sh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -e ." >&2
    exit 1
fi

# Activate virtual environment and run the MCP server
source venv/bin/activate
exec python -m pdf_mcp.server