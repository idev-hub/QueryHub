# Migration to UV

QueryHub has migrated from pip to [uv](https://docs.astral.sh/uv/) for dependency management. This document explains the changes and how to update your local development environment.

## What is uv?

uv is an extremely fast Python package installer and resolver written in Rust. It's 10-100x faster than pip and provides:

- ⚡️ **Speed**: Parallel downloads and installs
- 🔒 **Reliability**: Deterministic dependency resolution with lockfiles
- 🎯 **Compatibility**: Drop-in replacement for pip and venv
- 📦 **Modern**: Built-in virtual environment management

## For Existing Contributors

If you have an existing checkout, follow these steps to migrate:

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (if you prefer)
pip install uv
```

### 2. Remove old virtual environment

```bash
# Deactivate if currently active
deactivate

# Remove old venv
rm -rf .venv
```

### 3. Create new environment with uv

```bash
# Create virtual environment and install all dependencies
uv sync --all-extras

# Activate the environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

### 4. Verify installation

```bash
# Run checks to verify everything works
make check

# Or manually
ruff check
mypy src
pytest -m "not integration"
```

## Command Mapping

Here's how common pip commands map to uv:

| Old (pip) | New (uv) | Purpose |
|-----------|----------|---------|
| `pip install -e .[dev]` | `uv sync --all-extras` | Install package with all extras |
| `pip install -e .` | `uv sync` | Install package (production) |
| `pip install package` | `uv add package` | Add new dependency |
| `pip install --upgrade package` | `uv add package@latest` | Upgrade package |
| `pip freeze` | `uv pip freeze` | List installed packages |
| `python -m venv .venv` | `uv venv` | Create virtual environment |
| `pip list --outdated` | `uv pip list --outdated` | Check for updates |

## Makefile Changes

The Makefile targets have been updated:

```bash
# Old way (still works in a pinch)
pip install -e .[dev]

# New way (recommended)
make install           # Installs with uv sync --all-extras
uv sync --all-extras   # Or run directly
```

## CI/CD Changes

GitHub Actions workflows now use `astral-sh/setup-uv@v5` instead of `actions/setup-python`:

```yaml
# Old
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
- run: pip install -e .[dev]

# New
- uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
- run: uv python install 3.11
- run: uv sync --all-extras
```

## Benefits of uv

### Speed

Initial install comparison:
- pip: ~60 seconds
- uv: ~5 seconds (12x faster!)

Subsequent installs (with cache):
- pip: ~30 seconds
- uv: ~1 second (30x faster!)

### Lockfile

`uv.lock` ensures deterministic builds:
- Everyone gets the same dependency versions
- CI builds are reproducible
- No more "works on my machine" issues

### Better Error Messages

uv provides clearer conflict resolution messages when dependencies have incompatible requirements.

## Troubleshooting

### uv not found after installation

Add uv to your PATH:

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Then reload
source ~/.zshrc  # or ~/.bashrc
```

### Missing system dependencies (Linux)

Some packages like Kaleido need system libraries:

```bash
# Ubuntu/Debian
sudo apt-get install libglib2.0-0 libnss3 libfontconfig1

# Fedora/RHEL
sudo dnf install glib2 nss fontconfig
```

### Cache issues

If you encounter strange errors, try clearing uv's cache:

```bash
uv cache clean
uv sync --all-extras
```

### Want to use pip temporarily?

You can still use pip inside the uv-created venv:

```bash
source .venv/bin/activate
pip install some-package
```

But remember: this bypasses the lockfile and may cause inconsistencies.

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [Why uv?](https://astral.sh/blog/uv)
- [Python Packaging with uv](https://docs.astral.sh/uv/guides/projects/)

## Questions?

If you encounter issues during migration, please:
1. Check the [uv documentation](https://docs.astral.sh/uv/)
2. Search existing [GitHub issues](https://github.com/isasnovich/QueryHub/issues)
3. Open a new issue with details about your environment and error messages
