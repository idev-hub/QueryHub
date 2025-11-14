.PHONY: help docker-up docker-down docker-logs docker-ps test-integration test-integration-verbose test-all test-unit clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

docker-up: ## Start Docker test containers
	docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@for i in {1..30}; do \
		docker exec queryhub-test-postgres pg_isready -U testuser -d testdb 2>/dev/null && break || sleep 1; \
	done
	@echo "✅ PostgreSQL is ready"

docker-down: ## Stop and remove Docker test containers
	docker-compose -f docker-compose.test.yml down

docker-down-v: ## Stop and remove Docker test containers with volumes
	docker-compose -f docker-compose.test.yml down -v

docker-logs: ## Show Docker container logs
	docker-compose -f docker-compose.test.yml logs

docker-logs-follow: ## Follow Docker container logs
	docker-compose -f docker-compose.test.yml logs -f

docker-ps: ## Show Docker container status
	docker-compose -f docker-compose.test.yml ps

docker-restart: ## Restart Docker test containers
	docker-compose -f docker-compose.test.yml restart

test-integration: docker-up ## Run integration tests with Docker
	pytest tests/test_docker_integration.py -v -m integration

test-integration-verbose: docker-up ## Run integration tests with verbose output
	pytest tests/test_docker_integration.py -v -s -m integration

test-integration-specific: docker-up ## Run specific integration test (use TEST=test_name)
	pytest tests/test_docker_integration.py::$(TEST) -v -s

test-unit: ## Run unit tests only (skip integration tests)
	pytest -m "not integration" -v

test-all: docker-up ## Run all tests including integration tests
	pytest -v

test-coverage: docker-up ## Run tests with coverage report
	pytest --cov=src/queryhub --cov-report=html --cov-report=term -v

lint: ## Run linting
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/

typecheck: ## Run type checking
	mypy src/

check: lint typecheck ## Run all checks (lint + typecheck)

clean: ## Clean up temporary files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage

install: ## Install package in development mode
	pip install -e ".[dev]"

install-prod: ## Install package in production mode
	pip install -e .

# Integration test shortcuts
postgres-shell: ## Open PostgreSQL shell
	docker exec -it queryhub-test-postgres psql -U testuser -d testdb

postgres-query: ## Run a PostgreSQL query (use QUERY="SELECT ...")
	docker exec queryhub-test-postgres psql -U testuser -d testdb -c "$(QUERY)"

# Example integration test commands
.PHONY: example-report example-sales example-test

example-sales: docker-up ## Run example sales report generation
	@export POSTGRES_DSN="postgresql+asyncpg://testuser:testpass@localhost:5433/testdb" && \
	queryhub execute-report \
		--config-dir tests/fixtures/docker_integration \
		--templates-dir templates \
		sales_dashboard

example-test: ## Show test data counts
	@echo "Sales Metrics:"
	@docker exec queryhub-test-postgres psql -U testuser -d testdb -c "SELECT COUNT(*) FROM sales_metrics;"
	@echo "\nCustomer Feedback:"
	@docker exec queryhub-test-postgres psql -U testuser -d testdb -c "SELECT COUNT(*) FROM customer_feedback;"
	@echo "\nSystem Health:"
	@docker exec queryhub-test-postgres psql -U testuser -d testdb -c "SELECT COUNT(*) FROM system_health;"
