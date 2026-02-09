---
description: Run tests using the virtual environment
---

# Running Tests with Virtual Environment

This project uses a Python virtual environment (`venv`) to manage dependencies.

## Prerequisites

Ensure the virtual environment is created and dependencies are installed:

```bash
# Create venv if it doesn't exist
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

// turbo-all

Always activate the virtual environment before running tests:

```bash
# Activate venv and run all tests
source venv/bin/activate && pytest -v

# Run specific test files
source venv/bin/activate && pytest tests/test_domain.py tests/test_datasets.py -v

# Run with coverage
source venv/bin/activate && pytest --cov=src --cov-report=html
```

## Running Linters

```bash
# Run ruff checks
source venv/bin/activate && ruff check .

# Auto-fix issues
source venv/bin/activate && ruff check . --fix

# Format code
source venv/bin/activate && black .
```

## Important Notes

- **Always use `source venv/bin/activate &&` prefix** when running Python commands
- The system Python (3.9) is different from the venv Python (3.14)
- Running `pytest` directly without activating venv will use Python 3.9 and fail with syntax errors
