# VS Code Configuration

This directory contains VS Code configuration files to provide an optimal development experience for the PDF MCP project.

## Features Configured

### Settings (`settings.json`)
- **Python Environment**: Automatically uses `./venv/bin/python`
- **Code Formatting**: Black formatter with format-on-save
- **Import Sorting**: isort with black profile
- **Linting**: MyPy type checking enabled
- **Testing**: Pytest integration with test discovery
- **File Exclusions**: Hides build artifacts and cache files

### Launch Configurations (`launch.json`)
- **Run PDF MCP Server**: Launch the server directly
- **Test Parser**: Test parser with sample PDF
- **Run Tests**: Execute test suite with verbose output
- **Run Tests with Coverage**: Execute tests with coverage reporting

### Tasks (`tasks.json`)
Available tasks (accessible via `Ctrl+Shift+P` → "Tasks: Run Task"):
- `format` - Auto-format code with black/isort
- `lint` - Check code with ruff
- `typecheck` - Type check with mypy
- `test` - Run test suite
- `test-cov` - Run tests with coverage
- `quality` - Run all quality checks
- `install-dev` - Install development dependencies

### Recommended Extensions (`extensions.json`)
VS Code will suggest installing these extensions:
- Python extension pack (syntax, debugging, testing)
- MyPy type checker
- Black formatter
- isort import sorter
- Ruff linter
- Code spell checker
- Makefile tools

## Quick Start
1. Open this folder in VS Code
2. Install recommended extensions when prompted
3. VS Code will automatically detect the virtual environment
4. Use `F5` to run configurations or `Ctrl+Shift+P` → "Tasks" for build tasks

## Keyboard Shortcuts
- `F5` - Start debugging (run server)
- `Ctrl+Shift+P` → "Python: Run Tests" - Run all tests
- `Ctrl+Shift+P` → "Tasks: Run Task" - Access build tasks
- `Ctrl+S` - Auto-format and organize imports on save