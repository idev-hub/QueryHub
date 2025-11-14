# Docker Integration Tests - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Start Docker Containers
```bash
# Using the helper script (recommended)
./scripts/integration_test.sh start

# Or using make
make docker-up

# Or using docker-compose directly
docker-compose -f docker-compose.test.yml up -d
```

### 2. Run Integration Tests
```bash
# Using the helper script
./scripts/integration_test.sh test

# Or using make
make test-integration

# Or using pytest directly
pytest tests/test_docker_integration.py -v -m integration
```

### 3. View Results
The tests will:
- ✅ Connect to PostgreSQL container
- ✅ Execute SQL queries against test data
- ✅ Render HTML reports with multiple components
- ✅ Validate report content and data accuracy

### 4. Clean Up
```bash
# Stop containers
./scripts/integration_test.sh stop

# Or remove everything including volumes
./scripts/integration_test.sh cleanup
```

## 📋 Available Commands

### Helper Script Commands
```bash
./scripts/integration_test.sh start      # Start containers and verify data
./scripts/integration_test.sh stop       # Stop containers
./scripts/integration_test.sh cleanup    # Stop and remove volumes
./scripts/integration_test.sh test       # Run all integration tests
./scripts/integration_test.sh verify     # Verify test data exists
./scripts/integration_test.sh shell      # Open PostgreSQL shell
./scripts/integration_test.sh report     # Generate sample report
./scripts/integration_test.sh logs       # Show container logs
./scripts/integration_test.sh status     # Show container status
./scripts/integration_test.sh help       # Show all commands
```

### Make Commands
```bash
make docker-up                # Start containers
make docker-down              # Stop containers
make docker-logs              # View logs
make test-integration         # Run integration tests
make test-unit                # Run only unit tests
make test-all                 # Run all tests
make postgres-shell           # Open PostgreSQL shell
make example-sales            # Generate example report
make example-test             # Show test data counts
```

## 🔍 What Gets Tested

### Test Coverage
1. **Database Connectivity** - Validates PostgreSQL connection and schema
2. **Query Execution** - Tests various SQL queries with real data
3. **Report Rendering** - Generates complete HTML reports
4. **Parameterized Queries** - Tests SQL parameter binding
5. **Aggregations** - Complex analytics queries
6. **Concurrent Execution** - Multiple simultaneous queries
7. **Error Handling** - Provider failure scenarios

### Test Data
The PostgreSQL database includes:
- **sales_metrics**: 10 sales transactions across 3 regions, 2 products
- **customer_feedback**: 8 customer reviews with ratings
- **system_health**: 5 service health status records

### Report Components
The sample report includes:
1. Sales by Region (aggregated table)
2. Product Performance (revenue analysis)
3. Customer Satisfaction (ratings summary)
4. Recent Feedback (latest comments)
5. System Health Status (service monitoring)
6. Daily Sales Trend (chart data)

## 🧪 Running Specific Tests

```bash
# Run single test
pytest tests/test_docker_integration.py::test_postgres_sales_report -v

# Run with verbose output
pytest tests/test_docker_integration.py -v -s

# Run specific test pattern
pytest tests/test_docker_integration.py -k "sales" -v

# Skip integration tests (for regular development)
pytest -m "not integration"
```

## 🐛 Troubleshooting

### Containers won't start
```bash
# Check if Docker is running
docker info

# Check for port conflicts (PostgreSQL uses 5433)
lsof -i :5433

# View detailed logs
docker-compose -f docker-compose.test.yml logs postgres
```

### Tests fail with connection errors
```bash
# Verify container is healthy
docker ps | grep queryhub-test-postgres

# Check PostgreSQL is ready
docker exec queryhub-test-postgres pg_isready -U testuser -d testdb

# Restart containers
./scripts/integration_test.sh restart
```

### Test data is missing
```bash
# Verify test data
./scripts/integration_test.sh verify

# Or manually check
./scripts/integration_test.sh shell
# Then run: SELECT COUNT(*) FROM sales_metrics;
```

### Need to reset everything
```bash
# Clean up completely and start fresh
./scripts/integration_test.sh cleanup
./scripts/integration_test.sh start
```

## 📊 Manual Report Generation

Generate a sample report manually:

```bash
# Start containers
./scripts/integration_test.sh start

# Generate report using the helper script
./scripts/integration_test.sh report

# Or set environment and use CLI directly
export POSTGRES_DSN="postgresql+asyncpg://testuser:testpass@localhost:5434/testdb"
queryhub execute-report \
  --config-dir tests/fixtures/docker_integration \
  --templates-dir templates \
  sales_dashboard
```

## 🔧 Database Access

### PostgreSQL Shell
```bash
# Using helper script
./scripts/integration_test.sh shell

# Using make
make postgres-shell

# Or directly
docker exec -it queryhub-test-postgres psql -U testuser -d testdb
```

### Example Queries
```sql
-- Show all tables
\dt

-- Count records
SELECT COUNT(*) FROM sales_metrics;

-- Show recent sales
SELECT * FROM sales_metrics ORDER BY sale_date DESC LIMIT 5;

-- Revenue by region
SELECT region, SUM(revenue) as total 
FROM sales_metrics 
GROUP BY region 
ORDER BY total DESC;
```

## 📦 CI/CD Integration

The integration tests work in GitHub Actions:

```yaml
# .github/workflows/integration-tests.yml
- name: Start Docker containers
  run: docker-compose -f docker-compose.test.yml up -d

- name: Wait for PostgreSQL
  run: |
    for i in {1..30}; do
      docker exec queryhub-test-postgres pg_isready -U testuser && break
      sleep 1
    done

- name: Run integration tests
  run: pytest tests/test_docker_integration.py -v -m integration

- name: Stop containers
  if: always()
  run: docker-compose -f docker-compose.test.yml down -v
```

## 🎯 Next Steps

1. **Add More Tests**: See `tests/fixtures/docker_integration/README.md`
2. **Add ADX Support**: Configure Azure Data Explorer emulator
3. **Add SQL Server Tests**: Already configured in docker-compose
4. **Performance Testing**: Use concurrent test as baseline
5. **Custom Reports**: Create your own report configs in fixtures

## 📚 Related Documentation

- Full Integration Test Documentation: `tests/fixtures/docker_integration/README.md`
- Docker Compose Configuration: `docker-compose.test.yml`
- Test Data Schema: `tests/fixtures/docker/init-postgres.sql`
- Report Configuration: `tests/fixtures/docker_integration/reports/sales_dashboard.yaml`
- Test Implementation: `tests/test_docker_integration.py`

## 💡 Tips

- Use `make help` to see all available make targets
- Use `./scripts/integration_test.sh help` for script options
- Tests are marked with `@pytest.mark.integration`
- Skip integration tests locally: `pytest -m "not integration"`
- Check container health: `docker ps` should show "healthy" status
- Integration tests require ~10 seconds for first run (container startup)
- Subsequent test runs are faster (containers stay running)

---

**Happy Testing!** 🎉

For issues or questions, check the main README or open an issue on GitHub.
