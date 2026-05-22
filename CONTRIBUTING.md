# Contributing to Amazon Connect MCP Server

First off, thank you for considering contributing to the Amazon Connect MCP Server! It's people like you that make this project a great tool for the community.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to see if the problem has already been reported. If it has, add a comment to the existing issue instead of opening a new one.

When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed and what behavior you expected**
- **Include code samples and screenshots if relevant**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the enhancement**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repository
2. Create a new branch from `main` (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the test suite and ensure all tests pass
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- AWS CLI (optional, for testing with real AWS resources)

### Setup

```bash
# Clone your fork
git clone https://github.com/your-username/amazon-connect-mcp.git
cd amazon-connect-mcp

# Install development dependencies
uv pip install -e ".[dev,test]"

# Or with pip
pip install -e ".[dev,test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests (no AWS credentials required)
pytest -m unit

# Run integration tests (requires AWS credentials)
pytest -m integration
```

### Code Style

We use the following tools to maintain code quality:

```bash
# Formatting with Black
black src tests

# Linting with Ruff
ruff check src tests
ruff format src tests

# Type checking with mypy
mypy src

# Run all checks
black --check src tests && ruff check src tests && mypy src
```

### Pre-commit Hooks

We recommend setting up pre-commit hooks to run checks automatically:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files (optional)
pre-commit run --all-files
```

## Project Structure

```
amazon-connect-mcp/
├── src/
│   ├── amazon_connect_mcp/       # Main MCP server package
│   └── contact_flows/            # Contact flow tools
├── lambda/                       # Lambda functions
├── terraform/                    # Infrastructure as Code
├── tests/                        # Test suite
├── docs/                         # Documentation
└── examples/                     # Usage examples
```

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type hints for function signatures
- Write docstrings in Google style
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add support for custom contact flow templates

- Implement TemplateRegistry for user-defined templates
- Add validation for custom template parameters
- Update documentation with examples

Fixes #123
```

## Testing Guidelines

### Writing Tests

- Use pytest for all tests
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use descriptive test names that explain what is being tested

```python
def test_phone_numbers_search_returns_valid_response():
    """Test that phone_numbers_search returns expected response format."""
    # Test code here
```

### Test Markers

- Use `@pytest.mark.unit` for unit tests
- Use `@pytest.mark.integration` for tests requiring AWS credentials

### Mocking AWS Services

Use `moto` for mocking AWS services in unit tests:

```python
import boto3
from moto import mock_aws

@mock_aws
def test_connect_list_instances():
    client = boto3.client("connect", region_name="us-east-1")
    # Test code here
```

## Documentation

- Update the README.md if your changes affect user-facing functionality
- Update relevant documentation in the `docs/` directory
- Add docstrings to new functions and classes
- Include examples for new features

## Release Process

Maintainers will handle releases. The process includes:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a new release on GitHub
4. GitHub Actions will automatically publish to PyPI

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
