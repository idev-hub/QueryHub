#!/usr/bin/env bash
set -euo pipefail

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync --all-extras

echo ""
echo "✅ Setup complete! Virtual environment is activated."
echo "Run 'queryhub --help' to get started."
