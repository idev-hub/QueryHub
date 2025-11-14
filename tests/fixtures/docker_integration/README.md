# Docker Integration Tests

This directory contains Docker-based integration tests for QueryHub that test the full pipeline with real databases.

## Overview

The integration tests use Docker containers to:
- Run PostgreSQL database with test data
- Execute SQL queries through QueryHub providers
- Render complete HTML reports
- Validate the entire report generation pipeline

## Prerequisites

- Docker and Docker Compose installed
- Python dependencies installed (`pip install -e ".[dev]"`)

## Quick Start

### 1. Start Docker Containers

```bash
# Start PostgreSQL container
docker-compose -f docker-compose.test.yml up -d

# Check container status
docker-compose -f docker-compose.test.yml ps

# View logs if needed
docker-compose -f docker-compose.test.yml logs postgres
```

### 2. Run Integration Tests

```bash
# Run all integration tests
pytest tests/test_docker_integration.py -v

# Run specific test
pytest tests/test_docker_integration.py::test_postgres_sales_report -v

# Run with output
pytest tests/test_docker_integration.py -v -s

# Skip integration tests (useful for CI without Docker)
pytest -m "not integration"
```

### 3. Stop Containers

```bash
# Stop and remove containers
docker-compose -f docker-compose.test.yml down

# Stop and remove containers with volumes
docker-compose -f docker-compose.test.yml down -v
```

## Test Structure

### Docker Services

**docker-compose.test.yml**
- `postgres`: PostgreSQL 16 on port 5433
- `sqlserver`: SQL Server 2022 on port 1434 (optional)

### Test Data

**tests/fixtures/docker/init-postgres.sql**
- Creates tables: `sales_metrics`, `customer_feedback`, `system_health`
- Inserts sample data for testing
- Creates indexes for performance

### Test Fixtures

**tests/fixtures/docker_integration/**
- `smtp.yaml`: Email configuration (localhost SMTP)
- `providers/providers.yaml`: Database provider configurations
- `reports/sales_dashboard.yaml`: Comprehensive test report with multiple components

### Integration Tests

**tests/test_docker_integration.py**
- `test_postgres_connection`: Basic connectivity and schema validation
- `test_postgres_sales_report`: Full report execution with multiple components
- `test_postgres_query_with_parameters`: Parameterized SQL queries
- `test_postgres_aggregation_queries`: Complex aggregation and analytics
- `test_concurrent_queries`: Concurrent query execution

## Test Report Components

The integration test report includes:

1. **Sales by Region**: Aggregated revenue and units by geographic region
2. **Product Performance**: Product-level sales metrics
3. **Customer Satisfaction**: Feedback ratings and sentiment
4. **Recent Feedback**: Latest customer comments
5. **System Health Status**: Service health monitoring
6. **Daily Sales Trend**: Time-series chart data

## Manual Testing

You can manually test the report generation:

```bash
# Start containers
docker-compose -f docker-compose.test.yml up -d

# Set environment variable
export POSTGRES_DSN="postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"

# Run QueryHub CLI
queryhub execute-report \
  --config-dir tests/fixtures/docker_integration \
  --templates-dir templates \
  sales_dashboard
```

## Troubleshooting

### Containers won't start
```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :5433
lsof -i :1434

# View detailed logs
docker-compose -f docker-compose.test.yml logs
```

### PostgreSQL not ready
```bash
# Check health status
docker inspect queryhub-test-postgres | grep Health

# Connect manually
psql postgresql://testuser:testpass@localhost:5434/testdb

# Run test queries
psql postgresql://testuser:testpass@localhost:5434/testdb -c "SELECT COUNT(*) FROM sales_metrics;"
```

### Tests fail with connection errors
```bash
# Verify container is running and healthy
docker-compose -f docker-compose.test.yml ps

# Restart containers
docker-compose -f docker-compose.test.yml restart

# Check Python has asyncpg installed
python -c "import asyncpg; print(asyncpg.__version__)"
```

## CI/CD Integration

For GitHub Actions or other CI systems:

```yaml
# Example GitHub Actions workflow
- name: Start Docker containers
  run: docker-compose -f docker-compose.test.yml up -d

- name: Wait for PostgreSQL
  run: |
    for i in {1..30}; do
      docker exec queryhub-test-postgres pg_isready -U testuser && break
      sleep 1
    done

- name: Run integration tests
  run: pytest tests/test_docker_integration.py -v

- name: Stop containers
  run: docker-compose -f docker-compose.test.yml down
  if: always()
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_DSN` | PostgreSQL connection string | `postgresql+asyncpg://testuser:testpass@localhost:5434/testdb` |

## Adding New Tests

1. Add test data to `tests/fixtures/docker/init-postgres.sql`
2. Create report configuration in `tests/fixtures/docker_integration/reports/`
3. Add test function to `tests/test_docker_integration.py`
4. Mark with `@pytest.mark.integration`
5. Use `containers_ready` fixture to ensure Docker is available

Example:
```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_my_new_report(containers_ready: bool, monkeypatch) -> None:
    """Test description."""
    config_dir = Path("tests/fixtures/docker_integration")
    templates_dir = Path("templates")
    
    dsn = "postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
    monkeypatch.setenv("POSTGRES_DSN", dsn)
    
    executor = await ReportExecutor.from_config_dir(config_dir, templates_dir)
    try:
        result = await executor.execute_report("my_report_id")
        assert not result.has_failures
    finally:
        await executor.shutdown()
```

## Performance Testing

The concurrent test demonstrates connection pooling:

```python
# Execute multiple reports simultaneously
tasks = [executor.execute_report("sales_dashboard") for _ in range(10)]
results = await asyncio.gather(*tasks)
```

This validates that SQLAlchemy's connection pool handles concurrent requests efficiently.
