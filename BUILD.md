# Building QueryHub with Docker

This guide explains how to build a standalone, self-contained executable distribution of QueryHub using Docker. The build process creates a portable binary that works on Linux, macOS, and Windows without requiring Python installation.

## 📋 Prerequisites

### Required Software
- **Docker** (version 20.10 or later)
  - Linux: `apt-get install docker.io` or `yum install docker`
  - macOS: [Docker Desktop for Mac](https://docs.docker.com/desktop/mac/install/)
  - Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/)

### System Requirements
- **Disk Space**: ~2GB for Docker images and build artifacts
- **Memory**: 4GB RAM recommended
- **OS**: Linux, macOS, or Windows with WSL2

### Verify Docker Installation
```bash
# Check Docker version
docker --version

# Verify Docker is running
docker info
```

## 🏗️ Build Architecture

QueryHub uses a **multi-stage Docker build** for efficient, reproducible builds:

```
Stage 1: Builder
├── Install Python 3.11
├── Install system dependencies (gcc, make, libpq)
├── Install Python packages via uv
└── Install project dependencies

Stage 2: Packager
├── Create PyInstaller spec
├── Bundle application + dependencies
└── Generate standalone executable

Stage 3: Distribution
├── Copy executable
├── Copy templates & configs
├── Generate documentation
└── Create wrapper scripts
```

### Why Docker?

- ✅ **Reproducible builds** - Same result every time
- ✅ **No local Python required** - Build in isolated environment
- ✅ **Consistent dependencies** - Locked versions
- ✅ **Easy CI/CD integration** - Works in automated pipelines
- ✅ **Cross-platform** - Build from any OS

## 🚀 Quick Build

### Option 1: Using the Build Script (Recommended)

The easiest way to build:

```bash
# Clone the repository
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub

# Run the build script
./scripts/build_docker.sh

# Distribution will be in ./dist/
```

The script will:
1. Validate Docker installation
2. Build the Docker image
3. Extract distribution files
4. Set executable permissions
5. Create a timestamped archive

### Option 2: Using Make

```bash
# Build distribution
make build-dist

# Build and create archive
make build-archive

# Clean previous builds
make clean-dist
```

### Option 3: Manual Docker Build

```bash
# Build the Docker image
docker build --target packager-dist --tag queryhub-dist:latest .

# Create container to extract files
docker create --name queryhub-extract queryhub-dist:latest

# Extract distribution
docker cp queryhub-extract:/. ./dist/

# Clean up
docker rm queryhub-extract

# Make executable
chmod +x dist/queryhub dist/queryhub.sh
```

## 📦 Build Output

After building, you'll find in `./dist/`:

```
dist/
├── queryhub              # Linux/macOS executable (~150MB)
├── queryhub.exe          # Windows executable (if cross-compiled)
├── queryhub.sh           # Unix wrapper script
├── queryhub.bat          # Windows batch script
├── config/
│   ├── smtp/
│   │   └── default.yaml  # SMTP configuration
│   ├── templates/
│   │   └── report.html.j2
│   ├── providers/
│   │   ├── credentials.yaml
│   │   ├── 01_databases.yaml
│   │   └── 02_azure.yaml
│   └── reports/
│       └── sample_report/
│           ├── metadata.yaml
│           └── 01_component.yaml
├── README.md
├── DISTRIBUTION.md
├── CHANGELOG.md
├── LICENSE
└── VERSION.txt
```

## 🔧 Build Configuration

### Dockerfile Overview

```dockerfile
# Stage 1: Builder - Install Python and dependencies
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y gcc g++ make libpq-dev
COPY pyproject.toml src/ ./
RUN uv pip install [dependencies]

# Stage 2: Packager - Create executable
FROM builder as packager
RUN pyinstaller --onefile queryhub.spec

# Stage 3: Distribution - Assemble final package
FROM alpine:latest as packager-dist
COPY --from=packager /build/dist/queryhub ./
COPY config/ README.md ./
```

### Customizing the Build

#### Change Python Version
Edit `Dockerfile`:
```dockerfile
FROM python:3.12-slim as builder  # Change version here
```

#### Add System Dependencies
For additional libraries:
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    libffi-dev \
    your-package-here \
    && rm -rf /var/lib/apt/lists/*
```

#### Include Additional Files
In the `packager-dist` stage:
```dockerfile
COPY config/ ./config/
COPY docs/ ./docs/
```

#### Optimize Size
```dockerfile
# Use Alpine for smaller base
FROM python:3.11-alpine as builder

# Strip debug symbols
RUN strip dist/queryhub
```

## 🎯 Build Options

### Development Build (Faster)

For testing, skip optimization:

```bash
docker build \
  --target packager-dist \
  --build-arg OPTIMIZE=false \
  --tag queryhub-dev:latest \
  .
```

### Production Build (Optimized)

Full optimization with UPX compression:

```bash
docker build \
  --target packager-dist \
  --build-arg OPTIMIZE=true \
  --tag queryhub-prod:latest \
  .
```

### Build for Specific Platform

```bash
# For Linux ARM64
docker build --platform linux/arm64 -t queryhub-arm64:latest .

# For Linux AMD64
docker build --platform linux/amd64 -t queryhub-amd64:latest .
```

## 🔍 Troubleshooting Builds

### Build Fails: "No space left on device"

Clean up Docker:
```bash
docker system prune -a --volumes
```

### Build Fails: "Cannot connect to Docker daemon"

Start Docker:
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Start Docker Desktop application
```

### Executable Crashes on Startup

Check hidden imports in PyInstaller spec:
```python
hiddenimports=[
    'asyncpg',
    'aiohttp',
    # Add missing modules here
],
```

### Missing Templates/Config Files

Verify in Dockerfile `packager-dist` stage:
```dockerfile
COPY config ./config
# Templates are now in config/templates/
# SMTP configs are now in config/smtp/
```

### Import Errors in Executable

Add to `hiddenimports` in Dockerfile:
```python
hiddenimports=[
    'queryhub.providers.adx',
    'queryhub.providers.sql',
    # Your module here
],
```

## 🧪 Testing the Build

### Test Inside Docker

```bash
# Run executable in container
docker run --rm -it queryhub-dist:latest sh
/ # ./queryhub --help
```

### Test Locally

```bash
cd dist/

# Test help
./queryhub --help

# Test list reports
./queryhub list-reports config

# Test execution (no email)
export POSTGRES_USER=test
export POSTGRES_PASSWORD=test
./queryhub run-report config/reports/sample_report \
  --no-email \
  --output-html test.html
```

### Validate Package Contents

```bash
# Check executable
file dist/queryhub

# Check dependencies
ldd dist/queryhub  # Linux

# Check size
du -sh dist/
```

## 🚢 Distribution

### Create Archive

```bash
# Tar.gz (Linux/macOS)
cd dist/
tar -czf queryhub-$(date +%Y%m%d).tar.gz .

# Zip (Windows)
zip -r queryhub-$(date +%Y%m%d).zip .
```

### Upload to Release

```bash
# GitHub Releases
gh release create v0.1.0 \
  dist/queryhub-*.tar.gz \
  --title "QueryHub v0.1.0" \
  --notes "Standalone executable distribution"

# Or manually at:
# https://github.com/your-org/QueryHub/releases/new
```

## 🔄 CI/CD Integration

### GitHub Actions

Create `.github/workflows/build.yml`:

```yaml
name: Build Distribution

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build with Docker
        run: ./scripts/build_docker.sh
      
      - name: Create archive
        run: |
          cd dist
          tar -czf ../queryhub-${{ github.ref_name }}.tar.gz .
      
      - name: Upload Release Asset
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./queryhub-${{ github.ref_name }}.tar.gz
          asset_name: queryhub-${{ github.ref_name }}.tar.gz
          asset_content_type: application/gzip
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - ./scripts/build_docker.sh
    - cd dist && tar -czf ../queryhub-${CI_COMMIT_TAG}.tar.gz .
  artifacts:
    paths:
      - queryhub-*.tar.gz
  only:
    - tags
```

## 📊 Build Metrics

Typical build times and sizes:

| Metric | Value |
|--------|-------|
| Build Time | 5-10 minutes |
| Docker Image Size | ~1.5GB |
| Executable Size | ~150MB |
| Compressed Archive | ~45MB |
| Total Disk Usage | ~2GB (including cache) |

## 🔒 Security Considerations

### Best Practices

1. **Pin dependency versions** in `pyproject.toml`
2. **Scan for vulnerabilities**:
   ```bash
   docker scan queryhub-dist:latest
   ```
3. **Use official base images**
4. **Don't include secrets** in the image
5. **Sign releases** with GPG

### Verify Build Reproducibility

```bash
# Build twice
./scripts/build_docker.sh
mv dist dist1
./scripts/build_docker.sh
mv dist dist2

# Compare
diff -r dist1 dist2
```

## 🛠️ Advanced Topics

### Multi-Architecture Builds

Build for multiple architectures:

```bash
# Set up buildx
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target packager-dist \
  -t queryhub-multi:latest \
  --push \
  .
```

### Custom Build Arguments

```dockerfile
# In Dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim as builder
```

```bash
# Use in build
docker build --build-arg PYTHON_VERSION=3.12 .
```

### Layer Caching

Optimize build speed:

```dockerfile
# Copy requirements first (changes less often)
COPY pyproject.toml ./
RUN uv pip install -r requirements.txt

# Copy source later (changes more often)
COPY src/ ./src/
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Distribution Guide](./DISTRIBUTION.md)

## 💬 Getting Help

- **Build issues**: Open an issue on GitHub
- **Docker problems**: Check Docker documentation
- **PyInstaller issues**: Review PyInstaller docs
- **General questions**: See main README.md

## 📝 Changelog

Track build configuration changes:

- **2024-01**: Initial Docker build setup
- **2024-02**: Added multi-stage build
- **2024-03**: Optimized with Alpine Linux
- **2024-04**: Added cross-platform support

---

**Happy Building!** 🎉

For questions or issues, visit: https://github.com/isasnovich/QueryHub/issues
