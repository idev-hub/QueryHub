# Installation Guide

## Quick Start

```bash
# Basic installation (SQL, REST, CSV providers)
pip install queryhub

# With Azure services support
pip install queryhub[azure]

# With AWS services support
pip install queryhub[aws]

# With Google Cloud Platform support
pip install queryhub[gcp]

# With all cloud providers
pip install queryhub[cloud]

# Development installation with all dependencies
pip install queryhub[all]
```

## Provider-Specific Dependencies

QueryHub uses optional dependencies to keep the core installation lightweight. Only install what you need!

### Core Dependencies (Always Installed)

- `PyYAML` - Configuration file parsing
- `pydantic` - Configuration validation
- `Jinja2` - HTML template rendering
- `typer` - CLI interface
- `aiosmtplib` - Email sending
- `aiohttp` - REST API provider
- `SQLAlchemy[asyncio]` - SQL provider (PostgreSQL, MySQL, SQLite, MSSQL)
- `plotly` - Chart visualizations
- `pandas` - Data processing
- `numpy` - Numerical operations
- `kaleido` - Static image export

### Azure Services

```bash
pip install queryhub[azure]
```

**Includes:**
- `azure-kusto-data>=4.5` - Azure Data Explorer (Kusto) client
- `azure-identity>=1.15` - Azure authentication (DefaultAzureCredential, etc.)

**Supports:**
- Azure Data Explorer (Kusto/ADX)
- Azure Storage (Blob, Queue, Table) - ready to add
- Azure SQL Database - ready to add
- Azure Service Bus - ready to add
- Default Azure credentials (auto-discovery)
- Managed Identity
- Service Principal
- Connection strings
- Token-based auth

### AWS Services

```bash
pip install queryhub[aws]
```

**Includes:**
- `boto3>=1.34` - AWS SDK
- `aioboto3>=12.3` - Async AWS SDK

**Supports (ready to implement):**
- AWS S3
- AWS Athena
- AWS Redshift
- AWS DynamoDB
- AWS RDS
- Default AWS credential chain
- IAM roles
- Access key/secret

### Google Cloud Platform (GCP)

```bash
pip install queryhub[gcp]
```

**Includes:**
- `google-cloud-bigquery>=3.13` - BigQuery client
- `google-cloud-storage>=2.14` - Cloud Storage client
- `google-auth>=2.25` - GCP authentication

**Supports (ready to implement):**
- Google BigQuery
- Google Cloud Storage
- Google Pub/Sub
- Application Default Credentials (ADC)
- Service account keys

### All Cloud Providers

```bash
pip install queryhub[cloud]
```

Installs all cloud provider dependencies (Azure, AWS, GCP).

### Development

```bash
pip install queryhub[dev]
```

**Includes:**
- `pytest` - Testing framework
- `ruff` - Fast Python linter
- `mypy` - Static type checker
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `bandit` - Security linter
- `safety` - Dependency vulnerability scanner

### Everything

```bash
pip install queryhub[all]
```

Installs all optional dependencies (cloud providers + development tools).

## Platform-Specific Installation

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install QueryHub with desired providers
pip install queryhub[cloud]
```

### macOS

```bash
# Using Homebrew
brew install python3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install QueryHub
pip install queryhub[cloud]
```

### Windows

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install QueryHub
pip install queryhub[cloud]
```

## Docker Installation

### Using Pre-built Image

```bash
docker pull queryhub/queryhub:latest
docker run -v $(pwd)/config:/app/config queryhub/queryhub run-report daily_sales
```

### Building from Source

```bash
# Clone repository
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub

# Build with all cloud providers
docker build -t queryhub:latest .

# Or build with specific providers only
docker build --build-arg INSTALL_EXTRAS="adx" -t queryhub:adx .
```

## Verifying Installation

### Check Version

```bash
queryhub --version
```

### Check Available Providers

```bash
queryhub list-providers
```

### Run Tests

```bash
# Install with dev dependencies
pip install queryhub[all]

# Run tests
pytest tests/
```

## Cloud Provider Authentication Setup

### Azure (ADX)

**Option 1: Default Credentials (Recommended)**

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Verify
az account show
```

**Option 2: Service Principal**

```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
```

### AWS

**Option 1: Default Credentials**

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure
aws configure
```

**Option 2: Environment Variables**

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Google Cloud (GCP)

**Option 1: Application Default Credentials**

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and login
gcloud init
gcloud auth application-default login
```

**Option 2: Service Account Key**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Troubleshooting

### ImportError: No module named 'azure'

You need Azure dependencies:

```bash
pip install queryhub[azure]
```

### ImportError: No module named 'boto3'

You need AWS dependencies:

```bash
pip install queryhub[aws]
```

### ImportError: No module named 'google.cloud'

You need GCP dependencies:

```bash
pip install queryhub[gcp]
```

### SSL Certificate Errors

Install system certificates:

```bash
# Ubuntu/Debian
sudo apt-get install ca-certificates

# macOS
pip install --upgrade certifi
```

### Performance Issues

Install optional performance packages:

```bash
pip install uvloop  # Faster event loop
pip install orjson  # Faster JSON parsing
```

## Upgrading

```bash
# Upgrade to latest version
pip install --upgrade queryhub

# Upgrade with all extras
pip install --upgrade queryhub[all]
```

## Uninstalling

```bash
pip uninstall queryhub
```

## Minimum Requirements

- **Python**: 3.10 or higher
- **Memory**: 512 MB minimum, 2 GB recommended
- **Disk**: 100 MB for installation, more for data/reports
- **Network**: Required for cloud provider access

## Recommended Setup for Production

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash queryhub

# Create virtual environment
sudo -u queryhub python3 -m venv /opt/queryhub/venv

# Install with cloud providers
sudo -u queryhub /opt/queryhub/venv/bin/pip install queryhub[cloud]

# Set up systemd service
sudo systemctl enable queryhub
sudo systemctl start queryhub
```

## Getting Help

- **Documentation**: https://github.com/isasnovich/QueryHub
- **Issues**: https://github.com/isasnovich/QueryHub/issues
- **Discussions**: https://github.com/isasnovich/QueryHub/discussions
