# QueryHub Docker Integration Test Architecture

## Overview

Comprehensive Docker-based integration test suite that validates QueryHub with real PostgreSQL databases.

## System Architecture

```mermaid
graph TB
    subgraph Developer["Developer Machine"]
        subgraph Test["Test Execution Layer"]
            pytest["pytest CLI: -m integration -v -s"]
            make["Make targets: make test-int, make docker-up"]
            script["Helper Script: ./scripts/integration_test.sh"]
        end
        
        subgraph TestImpl["Test Implementation"]
            test_file["test_docker_integration.py"]
            steps["1. Check Docker | 2. Wait for PostgreSQL | 3. Load config | 4. Create ReportExecutor | 5. Execute report | 6. Validate results | 7. Cleanup"]
            test_file --> steps
        end
        
        subgraph App["QueryHub Application"]
            config["ConfigLoader"]
            executor["ReportExecutor"]
            template["TemplateEngine"]
            
            config --> provider_conf["ProviderConfig"]
            executor --> sql_provider["SQLProvider"]
            template --> jinja["Jinja2 Env"]
        end
        
        Test --> TestImpl
        TestImpl --> App
    end
    
    App -->|"SQL Queries via asyncpg/SQLAlchemy Port 5433"| Docker
    
    subgraph Docker["Docker Environment"]
        subgraph PG["PostgreSQL Container: queryhub-test-postgres"]
            pg16["PostgreSQL 16"]
            
            subgraph DB["Database: testdb User: testuser"]
                sales["sales_metrics: 10 rows"]
                feedback["customer_feedback: 8 rows"]
                health["system_health: 5 rows"]
            end
            
            pg16 --> DB
            init["init.sql: Schema & Data"] -.->|Initialize| DB
        end
        
        health_check["Health Check: pg_isready"] -.->|Monitor| PG
    end
    
    style Developer fill:#e1f5ff
    style Docker fill:#fff4e1
    style Test fill:#e1ffe1
    style TestImpl fill:#ffe1f5
    style App fill:#f5e1ff
    style PG fill:#ffe1e1
```

## Test Data Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Docker as Docker Compose
    participant PG as PostgreSQL
    participant Test as pytest
    participant QH as QueryHub
    
    Dev->>Docker: docker-compose up -d
    Docker->>PG: Start container
    Docker->>PG: Mount init-postgres.sql
    PG->>PG: Execute SQL (create tables + insert data)
    PG->>Docker: Ready
    
    Dev->>Test: pytest test_docker_integration.py
    Test->>Docker: Check containers running
    Test->>PG: Wait for ready (pg_isready)
    Test->>Test: Set POSTGRES_DSN env var
    
    Test->>QH: Load config from fixtures
    QH->>QH: Parse smtp.yaml
    QH->>QH: Parse providers.yaml
    QH->>QH: Parse sales_dashboard.yaml
    
    Test->>QH: Execute report
    QH->>PG: Execute 6 component queries
    PG->>QH: Return results
    QH->>QH: Render components
    QH->>QH: Compile HTML report
    QH->>Test: Return result
    
    Test->>Test: Validate results
    Test->>Test: Check HTML content
    Test->>Test: Verify data presence
    Test->>Test: Assert no failures
    
    Test->>QH: executor.shutdown()
    QH->>PG: Close connections
    Test->>Dev: Test results
    
    Dev->>Docker: docker-compose down (optional)
    Docker->>PG: Stop container
```

## Report Components

```mermaid
graph LR
    subgraph Report["sales_dashboard.yaml"]
        subgraph Tables["Table Components"]
            sales_region["sales_by_region: GROUP BY region"]
            product_perf["product_performance: GROUP BY product"]
            cust_sat["customer_satisfaction: AVG rating"]
            feedback["recent_feedback: LIMIT 5"]
            health["system_health: ORDER BY status"]
        end
        
        subgraph Charts["Chart Components"]
            daily["daily_sales: Line chart"]
        end
    end
    
    Report -->|"SQL Queries"| PG[("PostgreSQL testdb")]
    
    PG --> Data
    
    subgraph Data["Test Data"]
        sm["sales_metrics: 10 rows"]
        cf["customer_feedback: 8 rows"]
        sh["system_health: 5 rows"]
    end
    
    style Tables fill:#e1f5ff
    style Charts fill:#ffe1f5
    style Data fill:#fff4e1
```

## File Structure

```mermaid
graph TD
    Root[QueryHub/] --> Docker[docker-compose.test.yml]
    Root --> Make[Makefile]
    Root --> IntDoc[INTEGRATION_TESTS.md]
    
    Root --> GHA[.github/workflows/]
    GHA --> Workflow[integration-tests.yml]
    
    Root --> Scripts[scripts/]
    Scripts --> IntScript[integration_test.sh]
    Scripts --> Demo[demo_integration_tests.py]
    
    Root --> Tests[tests/]
    Tests --> TestFile[test_docker_integration.py]
    Tests --> Fixtures[fixtures/]
    
    Fixtures --> DockerFix[docker/]
    DockerFix --> InitSQL[init-postgres.sql]
    
    Fixtures --> IntFix[docker_integration/]
    IntFix --> README[README.md]
    IntFix --> SMTP[smtp.yaml]
    IntFix --> Prov[providers/]
    Prov --> ProvYAML[providers.yaml]
    IntFix --> Rep[reports/]
    Rep --> SalesDash[sales_dashboard.yaml]
    
    Root --> Docs[docs/reference/]
    Docs --> DocFile[docker-integration-tests.md]
    
    style Docker fill:#e1f5ff
    style TestFile fill:#ffe1f5
    style InitSQL fill:#fff4e1
    style SalesDash fill:#e1ffe1
```

## Test Coverage Matrix

```mermaid
mindmap
  root((Integration<br/>Tests))
    Database
      Connectivity
      Schema validation
      Query execution
      Connection pooling
      Health checks
    Queries
      Simple SELECT
      Parameterized
      Aggregations
      Joins & filters
      ORDER BY & LIMIT
    Report Generation
      Config loading
      Provider init
      Component execution
      HTML rendering
      Error handling
    Concurrency
      Simultaneous queries
      Connection management
      Thread safety
```

## Commands Quick Reference

### Test Execution
```bash
# Start & Test
./scripts/integration_test.sh start
./scripts/integration_test.sh test

# Make targets
make docker-up
make test-integration
make postgres-shell

# Pytest
pytest tests/test_docker_integration.py -v -m integration
pytest -m "not integration"  # Skip integration tests
```

### Docker Management
```bash
# Start/Stop
docker-compose -f docker-compose.test.yml up -d
docker-compose -f docker-compose.test.yml down

# Shell access
docker exec -it queryhub-test-postgres psql -U testuser -d testdb

# Logs
docker-compose -f docker-compose.test.yml logs postgres
```

## Performance Metrics

```mermaid
gantt
    title Test Execution Timeline
    dateFormat  s
    axisFormat %Ss
    
    section Cold Start
    Container startup    :a1, 0, 10s
    PostgreSQL ready     :a2, after a1, 3s
    Schema initialization:a3, after a2, 2s
    
    section Test Execution
    Report execution     :b1, after a3, 1s
    Validation          :b2, after b1, 1s
    Cleanup             :b3, after b2, 1s
    
    section Warm Run
    Test suite (warm)   :c1, after b3, 5s
```

**Typical Times:**
- **Cold start**: 15-20 seconds
- **Warm start**: 5-10 seconds  
- **Report execution**: 100-200ms
- **Full test suite**: 15-20 seconds (cold), 5-10 seconds (warm)

## Key Benefits

```mermaid
graph LR
    A[Integration Tests] --> B[Real Database]
    A --> C[Reproducible]
    A --> D[Portable]
    A --> E[Fast]
    A --> F[Comprehensive]
    A --> G[CI/CD Ready]
    A --> H[Developer Friendly]
    
    B --> B1[Not mocks]
    C --> C1[Same env every time]
    D --> D1[Runs anywhere with Docker]
    E --> E1[Quick feedback]
    F --> F1[Full pipeline]
    G --> G1[GitHub Actions]
    H --> H1[Easy to debug]
    
    style A fill:#e1f5ff
    style B fill:#e1ffe1
    style C fill:#ffe1f5
    style D fill:#fff4e1
    style E fill:#f5e1ff
    style F fill:#ffe1e1
    style G fill:#e1fff5
    style H fill:#f5ffe1
```

## Maintenance & Extension

### Adding New Tests

```mermaid
flowchart LR
    A[1. Add test data<br/>to init.sql] --> B[2. Create report<br/>config YAML]
    B --> C[3. Write test<br/>function]
    C --> D[4. Mark with<br/>@pytest.mark.integration]
    D --> E[5. Run and<br/>validate]
    
    style A fill:#e1f5ff
    style B fill:#ffe1f5
    style C fill:#fff4e1
    style D fill:#e1ffe1
    style E fill:#f5e1ff
```

### Troubleshooting Flow

```mermaid
flowchart TD
    Start[Test Failure] --> Q1{Container running?}
    Q1 -->|No| Fix1[docker-compose up -d]
    Q1 -->|Yes| Q2{PostgreSQL ready?}
    
    Q2 -->|No| Fix2[Wait longer<br/>Check logs]
    Q2 -->|Yes| Q3{Connection works?}
    
    Q3 -->|No| Fix3[Check DSN env var<br/>Check port 5433]
    Q3 -->|Yes| Q4{Data present?}
    
    Q4 -->|No| Fix4[Re-run init.sql<br/>Rebuild container]
    Q4 -->|Yes| Fix5[Check query syntax<br/>Check config files]
    
    Fix1 --> Retry[Retry test]
    Fix2 --> Retry
    Fix3 --> Retry
    Fix4 --> Retry
    Fix5 --> Retry
    
    style Start fill:#ffe1e1
    style Retry fill:#e1ffe1
```

## Summary

**What's Tested:**
- ✅ Real PostgreSQL database operations
- ✅ Full report generation pipeline  
- ✅ Complex SQL queries with aggregations
- ✅ Concurrent query execution
- ✅ Connection pooling
- ✅ Error handling

**What's Provided:**
- 🐳 Docker Compose setup
- 📊 Realistic test data
- 🧪 5 comprehensive test functions
- 🛠️ Helper scripts & Makefile targets
- 📚 Extensive documentation
- 🤖 GitHub Actions workflow

**Getting Started:**
```bash
./scripts/integration_test.sh start
./scripts/integration_test.sh test
```

---

*For detailed implementation guide, see: `INTEGRATION_TESTS.md`*  
*For fixture details, see: `tests/fixtures/docker_integration/README.md`*
