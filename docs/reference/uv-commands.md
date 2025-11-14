# UV Quick Reference

Common `uv` commands for QueryHub development.

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

## Environment Setup

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install all dependencies (including dev)
uv sync --all-extras

# Install only production dependencies
uv sync

# Install without updating lockfile
uv sync --frozen
```

## Dependency Management

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Add a specific version
uv add package-name==1.2.3

# Add with version constraint
uv add "package-name>=1.2.0,<2.0.0"

# Upgrade a package
uv add package-name@latest

# Remove a package
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Update lockfile only
uv lock --upgrade
```

## Running Commands

```bash
# Run command in managed environment (no activation needed)
uv run pytest
uv run python script.py
uv run queryhub --help

# Run with specific Python version
uv run --python 3.11 python script.py

# Install and run a tool temporarily
uvx ruff check
uvx black .
```

## Python Management

```bash
# Install Python version
uv python install 3.11

# List installed Python versions
uv python list

# Pin Python version for project
uv python pin 3.11
```

## Information & Debugging

```bash
# Show installed packages
uv pip list

# Show outdated packages
uv pip list --outdated

# Show package details
uv pip show package-name

# Export requirements
uv pip freeze > requirements.txt

# Check uv cache size
uv cache dir
uv cache clean
```

## Project Commands

```bash
# Initialize a new project
uv init

# Build the package
uv build

# Publish to PyPI
uv publish
```

## Makefile Shortcuts (QueryHub specific)

```bash
# Install dependencies
make install              # uv sync --all-extras

# Run checks
make lint                 # uv run ruff check
make typecheck            # uv run mypy src
make security             # uv run bandit -r src/
make check                # All checks

# Run tests
make test-unit            # uv run pytest -m "not integration"
make test-all             # uv run pytest
make test-coverage        # With coverage report

# Clean up
make clean                # Remove caches and temp files
```

## Troubleshooting

```bash
# Clear cache
uv cache clean

# Reinstall everything
rm -rf .venv uv.lock
uv sync --all-extras

# Verbose output for debugging
uv sync --verbose

# Check for conflicts
uv pip check
```

## Performance Tips

- **Cache**: uv automatically caches downloads in `~/.cache/uv`
- **Parallel**: Multiple packages install in parallel automatically
- **Lockfile**: `uv.lock` ensures consistent installs across machines
- **No activation needed**: Use `uv run` to skip manual activation

## Migration from pip

| pip | uv |
|-----|-----|
| `pip install package` | `uv add package` |
| `pip install -r requirements.txt` | `uv pip sync requirements.txt` |
| `pip install -e .` | `uv sync` |
| `pip install -e .[dev]` | `uv sync --all-extras` |
| `pip freeze` | `uv pip freeze` |
| `pip list` | `uv pip list` |
| `python -m venv .venv` | `uv venv` |

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub](https://github.com/astral-sh/uv)
- [QueryHub Migration Guide](./uv-migration.md)
