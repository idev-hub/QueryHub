# Contributing to QueryHub

Thanks for your interest in contributing! This document describes how to get started and the expectations for contributors.

## Getting started
- Fork the repository and clone your fork locally.
- Install [uv](https://docs.astral.sh/uv/) if you haven't already: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Install the project using `uv sync --all-extras` to make sure all development dependencies are available.
- Create a new branch for each change you plan to make.

## Development workflow
1. Make your changes in small, logical commits.
2. Run `make check` (or `uv run ruff check` and `uv run pytest`) locally to ensure the codebase stays healthy.
3. Update documentation and tests alongside code changes.
4. Open a pull request that clearly states the problem being solved and the solution you implemented.

## Running tests and checks
```bash
# Install dependencies
uv sync --all-extras

# Run all checks (recommended before committing)
make check

# Or run individually
uv run ruff check          # Linting
uv run mypy src            # Type checking
uv run bandit -r src/      # Security checks
uv run pytest              # Tests

# Run specific test files
uv run pytest tests/test_config_loader.py -v
```

## Code style and quality
- Follow the style enforced by Ruff and the Python standard library.
- Keep functions small and focused; prefer readability over cleverness.
- Add type hints where practical.
- Include or update tests whenever you fix a bug or add new features.

## Reporting bugs and requesting features
- Use the issue templates to provide as much context as possible.
- Search for existing issues before opening a new one to avoid duplicates.

## Community guidelines
- Be respectful and constructive in all interactions.
- Review the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

Thank you for helping improve QueryHub!
