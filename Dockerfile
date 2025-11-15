# Multi-stage Dockerfile for building QueryHub standalone executable
# This creates a portable binary that works on Linux, macOS, and Windows (via cross-compilation)

# =============================================================================
# Stage 1: Build environment with Python and dependencies
# =============================================================================
FROM python:3.11-slim as builder

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    binutils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy project files
COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY README.md LICENSE CHANGELOG.md ./

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install project dependencies (including PyInstaller)
RUN uv pip install --no-cache-dir \
    PyYAML>=6.0 \
    pydantic>=2.5 \
    Jinja2>=3.1 \
    typer>=0.12 \
    aiosmtplib>=2.0 \
    aiohttp>=3.9 \
    SQLAlchemy[asyncio]>=2.0 \
    asyncpg>=0.29 \
    azure-kusto-data>=4.5 \
    plotly>=5.18 \
    numpy>=1.24 \
    pandas>=2.0 \
    kaleido>=0.2 \
    python-dateutil>=2.8 \
    pyinstaller>=6.0

# Install the package itself
RUN uv pip install --no-cache-dir -e .

# =============================================================================
# Stage 2: Build executable with PyInstaller
# =============================================================================
FROM builder as packager

WORKDIR /build

# Create PyInstaller spec file
RUN echo "# -*- mode: python ; coding: utf-8 -*-\n\
\n\
block_cipher = None\n\
\n\
a = Analysis(\n\
    ['src/queryhub/__main__.py'],\n\
    pathex=[],\n\
    binaries=[],\n\
    datas=[\n\
        ('config/templates', 'templates'),\n\
        ('src/queryhub', 'queryhub'),\n\
    ],\n\
    hiddenimports=[\n\
        'queryhub',\n\
        'queryhub.cli',\n\
        'queryhub.config',\n\
        'queryhub.core',\n\
        'queryhub.email',\n\
        'queryhub.providers',\n\
        'queryhub.rendering',\n\
        'queryhub.services',\n\
        'asyncpg',\n\
        'aiohttp',\n\
        'aiosmtplib',\n\
        'azure.kusto.data',\n\
        'plotly',\n\
        'pandas',\n\
        'numpy',\n\
        'kaleido',\n\
        'sqlalchemy.dialects.postgresql',\n\
        'sqlalchemy.dialects.mysql',\n\
        'sqlalchemy.dialects.sqlite',\n\
    ],\n\
    hookspath=[],\n\
    hooksconfig={},\n\
    runtime_hooks=[],\n\
    excludes=[],\n\
    win_no_prefer_redirects=False,\n\
    win_private_assemblies=False,\n\
    cipher=block_cipher,\n\
    noarchive=False,\n\
)\n\
\n\
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n\
\n\
exe = EXE(\n\
    pyz,\n\
    a.scripts,\n\
    a.binaries,\n\
    a.zipfiles,\n\
    a.datas,\n\
    [],\n\
    name='queryhub',\n\
    debug=False,\n\
    bootloader_ignore_signals=False,\n\
    strip=False,\n\
    upx=True,\n\
    upx_exclude=[],\n\
    runtime_tmpdir=None,\n\
    console=True,\n\
    disable_windowed_traceback=False,\n\
    argv_emulation=False,\n\
    target_arch=None,\n\
    codesign_identity=None,\n\
    entitlements_file=None,\n\
)\n\
" > queryhub.spec

# Build the executable
RUN pyinstaller --clean --noconfirm queryhub.spec

# =============================================================================
# Stage 3: Create distribution package
# =============================================================================
FROM alpine:latest as packager-dist

WORKDIR /dist

# Copy executable from builder
COPY --from=packager /build/dist/queryhub ./queryhub

# Copy necessary files for distribution
COPY config ./config
COPY README.md LICENSE CHANGELOG.md ./

# Create distribution-specific README
RUN echo "# QueryHub - Standalone Distribution\n\
\n\
This is a standalone executable distribution of QueryHub.\n\
No Python installation required!\n\
\n\
## Quick Start\n\
\n\
### Linux/macOS\n\
\`\`\`bash\n\
# Make executable (first time only)\n\
chmod +x queryhub\n\
\n\
# Run a report\n\
./queryhub run-report config/reports/sample_report\n\
\`\`\`\n\
\n\
### Windows\n\
\`\`\`cmd\n\
queryhub.exe run-report config/reports/sample_report\n\
\`\`\`\n\
\n\
## Directory Structure\n\
\n\
- \`queryhub\` / \`queryhub.exe\` - The executable\n\
- \`config/\` - All configuration\n\
  - \`config/templates/\` - Jinja2 HTML templates\n\
  - \`config/smtp/\` - SMTP configurations\n\
  - \`config/providers/\` - Data source providers\n\
  - \`config/reports/\` - Report definitions (folder-based)\n\
- \`README.md\` - Full documentation\n\
- \`DISTRIBUTION.md\` - Distribution-specific guide\n\
\n\
## Configuration\n\
\n\
1. Copy \`config/\` to your working directory\n\
2. Edit YAML files to match your environment\n\
3. Set environment variables for secrets:\n\
   - SMTP_USERNAME, SMTP_PASSWORD\n\
   - POSTGRES_USER, POSTGRES_PASSWORD\n\
   - etc.\n\
\n\
## Commands\n\
\n\
\`\`\`bash\n\
# List available reports\n\
./queryhub list-reports config\n\
\n\
# Run report without sending email\n\
./queryhub run-report config/reports/REPORT_NAME --no-email --output-html output.html\n\
\n\
# Run with verbose logging\n\
./queryhub run-report config/reports/REPORT_NAME -v\n\
\n\
# Get help\n\
./queryhub --help\n\
./queryhub run-report --help\n\
\`\`\`\n\
\n\
For detailed documentation, see README.md\n\
" > DISTRIBUTION.md

# Create wrapper scripts for easier execution
RUN echo "#!/bin/sh\n\
# QueryHub wrapper script for Unix systems\n\
\n\
SCRIPT_DIR=\"\$(cd \"\$(dirname \"\$0\")\" && pwd)\"\n\
\"\$SCRIPT_DIR/queryhub\" \"\$@\"\n\
" > queryhub.sh && chmod +x queryhub.sh

RUN echo "@echo off\n\
REM QueryHub wrapper script for Windows\n\
\n\
set SCRIPT_DIR=%~dp0\n\
\"%SCRIPT_DIR%queryhub.exe\" %*\n\
" > queryhub.bat

# Create a version file
RUN echo "QueryHub v0.1.0\n\
Built: $(date -u +'%Y-%m-%d %H:%M:%S UTC')\n\
Platform: Linux x86_64\n\
Python: 3.11\n\
" > VERSION.txt

# =============================================================================
# Final stage: Output image with just the distribution
# =============================================================================
FROM scratch as output

COPY --from=packager-dist /dist /

# This allows extracting files with: docker cp
