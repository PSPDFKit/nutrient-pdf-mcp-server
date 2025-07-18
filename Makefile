# PDF MCP Development Tasks

# Auto-detect python and pip commands
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null || echo "python")
PIP := $(shell command -v pip3 2> /dev/null || command -v pip 2> /dev/null || echo "pip")

.PHONY: help install install-dev test test-unit test-integration test-cov lint format typecheck quality clean build serve

# Default target
help: ## Show this help message
	@echo "PDF MCP Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev    # Set up development environment"
	@echo "  make test           # Run all tests"
	@echo "  make quality        # Run all quality checks"
	@echo "  make serve          # Start the MCP server"

# Installation
install: ## Install package in production mode
	$(PIP) install .

install-dev: ## Install package in development mode with all dependencies
	$(PIP) install -e ".[dev]"

# Testing
test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m "not integration and not slow"

test-integration: ## Run integration tests only
	pytest -m "integration"

test-slow: ## Run slow tests only
	pytest -m "slow"

test-cov: ## Run tests with coverage report
	pytest --cov=pdf_mcp --cov-report=term-missing --cov-report=html

test-cov-fail: ## Run tests with coverage and fail if below 80%
	pytest --cov=pdf_mcp --cov-fail-under=80 --cov-report=term-missing

# Code Quality
lint: ## Run linter (ruff)
	ruff check .

lint-fix: ## Run linter and fix auto-fixable issues
	ruff check . --fix

format: ## Format code with black and isort
	black .
	isort .

format-check: ## Check if code is properly formatted
	black --check .
	isort --check .

typecheck: ## Run type checker (mypy)
	mypy pdf_mcp/

# Combined Quality Checks
quality: ## Run all quality checks (format, lint, typecheck, test)
	@echo "🔍 Checking code formatting..."
	black --check .
	isort --check .
	@echo "✅ Code formatting OK"
	@echo ""
	@echo "🔍 Running linter..."
	ruff check .
	@echo "✅ Linting OK"
	@echo ""
	@echo "🔍 Type checking..."
	mypy pdf_mcp/
	@echo "✅ Type checking OK"
	@echo ""
	@echo "🔍 Running tests..."
	pytest
	@echo "✅ All tests passed"
	@echo ""
	@echo "🎉 All quality checks passed!"

quality-fix: ## Run quality checks and fix what can be auto-fixed
	black .
	isort .
	ruff check . --fix
	mypy pdf_mcp/
	pytest

# Development
serve: ## Start the MCP server for development
	$(PYTHON) -m pdf_mcp.server

serve-debug: ## Start the MCP server with debug logging
	PYTHONPATH=. $(PYTHON) -c "import logging; logging.basicConfig(level=logging.DEBUG); from pdf_mcp.server import main; import asyncio; asyncio.run(main())"

# Testing with specific PDFs
test-sample: ## Test with sample PDF (requires res/document.pdf)
	$(PYTHON) test_direct.py res/document.pdf lazy
	$(PYTHON) test_direct.py res/document.pdf resolve "3-0" shallow

# Utilities
clean: ## Clean up build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build distribution packages
	$(PYTHON) -m build

# Development workflow helpers
dev-setup: install-dev ## Complete development environment setup
	@echo "✅ Development environment ready!"
	@echo "Try: make test"

pre-commit: quality ## Run all checks before committing
	@echo "🚀 Ready to commit!"

# Watch for changes (requires entr)
watch-test: ## Watch files and run tests on changes (requires 'entr')
	find pdf_mcp tests -name "*.py" | entr -c make test

watch-quality: ## Watch files and run quality checks on changes (requires 'entr')
	find pdf_mcp tests -name "*.py" | entr -c make quality