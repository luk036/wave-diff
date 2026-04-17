# wave-diff AGENTS.md

This file provides guidelines for agents operating in this repository.

## Project Overview

wave-diff is a Python library for waveform and text difference analysis using Levenshtein distance and Dynamic Time Warping (DTW). It requires Python 3.9+.

---

## Build, Lint, and Test Commands

### Installation
```bash
pip install -e .[testing]      # Install with test dependencies
```

### Running Tests
```bash
pytest                         # Run all tests with coverage
pytest tests/                  # Run specific test directory
pytest tests/test_diff.py      # Run specific test file
pytest -k test_name           # Run tests matching pattern
pytest --no-cov                # Run without coverage (faster)
pytest -v                     # Verbose output
pytest --lf                   # Run only last failed tests
```

### Running Linters/Formatters
```bash
ruff check .                  # Run ruff linter (auto-fixes: --fix)
flake8 .                      # Run flake8
black .                       # Run black formatter
isort .                       # Run isort import sorter

# Pre-commit hooks (recommended before commits)
pre-commit install            # Install hooks
pre-commit run                # Run all hooks
pre-commit run --all-files    # Run on all files
```

### Package Commands
```bash
pip install -e .              # Editable install
pip install -e .[testing]     # With test dependencies
```

---

## Code Style Guidelines

### Python Version
- Minimum: Python 3.9
- Target: Python 3.12 (for CI)

### Type Hints
- **Required** for all new code in `experiments/` module
- Use `typing` module for complex types (List, Dict, Tuple, Optional, Union)
- Example:
  ```python
  from typing import List, Tuple, Dict, Any

  def levenshtein_distance(str1: str, str2: str) -> Tuple[int, List[List[int]]]:
      ...
  ```

### Import Conventions
- Standard library imports first
- Third-party imports second
- Local imports third
- Separate with blank lines
- Use absolute imports:
  ```python
  from experiments.diff_distance import levenshtein_distance
  # NOT: from .diff_distance import ...
  ```

### Naming Conventions
- **Modules**: lowercase, short, descriptive (e.g., `diff_distance.py`)
- **Classes**: PascalCase (e.g., `EditOperation`)
- **Functions/variables**: snake_case (e.g., `levenshtein_distance`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_LENGTH`)
- **Private functions**: prefix with underscore (e.g., `_helper_function`)

### Formatting Rules (Black-compatible)
- Line length: 188 characters (configured in setup.cfg)
- Double quotes for strings unless containing double quotes
- No trailing whitespace
- LF line endings (enforced by pre-commit)
- Use trailing commas in multi-line calls

### Error Handling
- Use specific exception types
- Prefer explicit error messages
- Never use bare `except:` - specify exception type
- Example:
  ```python
  try:
      with open(filepath, "r", encoding="utf-8") as f:
          content = f.read()
  except FileNotFoundError as e:
      print(f"Error: File not found - {e.filename}", file=sys.stderr)
      sys.exit(1)
  ```

### Code Organization
- Keep functions small and focused (single responsibility)
- Group related functions into modules
- Put CLI entry points in `if __name__ == "__main__":` blocks
- Keep `experiments/` for library code, `tests/` for tests

### Documentation
- Use docstrings for public APIs
- Keep docstrings concise; focus on "what" and "why", not "how"
- Example:
  ```python
  def levenshtein_distance(str1: str, str2: str) -> Tuple[int, List[List[int]]]:
      """Calculate Levenshtein distance between two strings.

      Returns the distance and the edit operations matrix.
      """
  ```

### Testing Guidelines
- Test files go in `tests/` directory
- Name test files `test_*.py`
- Use pytest framework
- One assertion per test when possible
- Include doctests in modules (enabled via setup.cfg)

---

## Project Structure

```
wave-diff/
├── experiments/          # Main package code
│   ├── __init__.py      # Package init
│   ├── diff_distance.py # Levenshtein distance (main module)
│   ├── diff_tool.py     # Standard library diff wrappers
│   └── waveform_diff.py # Waveform comparison (DTW)
├── tests/               # Test files
│   ├── conftest.py      # Pytest fixtures
│   └── test_diff.py     # Test cases
├── setup.cfg            # Project configuration
├── setup.py             # Setup script
├── pyproject.toml       # Build configuration
├── README.md            # Documentation
└── .pre-commit-config.yaml  # Pre-commit hooks
```

---

## CI/CD Configuration

- **Test Matrix**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Lint Matrix**: Python 3.9, 3.12
- **Coverage Threshold**: 10% (minimum for experiments module)
- **Linters**: ruff, flake8, black, isort

---

## Common Tasks

### Running a Single Test
```bash
pytest tests/test_diff.py::test_levenshtein_identical
```

### Adding a New Experiment
1. Create file in `experiments/`
2. Add type hints
3. Add tests in `tests/`
4. Run `pytest` to verify

### Debugging
```bash
pytest --no-cov -v                    # Faster test runs
pytest -v --capture=no -s             # Show print statements
```

---

This file is used by AI agents to understand project conventions and operate effectively in this codebase.