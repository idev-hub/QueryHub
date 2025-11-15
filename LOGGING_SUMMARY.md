# Logging Implementation Summary

This document summarizes the comprehensive logging added to QueryHub to provide visibility into application progress and status.

## Overview

Industry-standard logging has been implemented throughout the QueryHub application using Python's built-in `logging` module. Logs are structured to provide clear progress tracking, error reporting, and debugging information.

## Logging Levels Used

- **INFO**: User-facing progress updates, major milestones, and successful operations
- **DEBUG**: Detailed technical information useful for debugging
- **WARNING**: Recoverable issues and retry attempts
- **ERROR**: Critical failures and exceptions

## Modules Enhanced with Logging

### 1. CLI (`src/queryhub/cli.py`)

**Added logging for:**
- Application startup and report execution initialization
- Configuration loading progress
- Report execution lifecycle
- Email sending operations
- Successful completion vs. failures
- Resource cleanup

**Example logs:**
```
INFO: Starting QueryHub report execution for report_id='daily_sales'
INFO: Initializing QueryHub application builder
INFO: Report 'Daily Sales Report' completed: 3/3 components successful
INFO: Email sent successfully
```

### 2. Configuration Loader (`src/queryhub/config/loader.py`)

**Added logging for:**
- Configuration file and directory reading
- SMTP, provider, report, and credential loading
- Number of entities loaded (providers, reports, credentials)
- Environment variable substitution

**Example logs:**
```
INFO: Loading QueryHub configuration from: /path/to/config
DEBUG: Loading provider configurations
INFO: Loaded 5 provider(s)
DEBUG: Registered provider: azure_adx (type=adx)
INFO: Loaded 3 report(s)
INFO: Configuration loaded successfully
```

### 3. Report Executor (`src/queryhub/services/executor.py`)

**Added logging for:**
- Report execution start and completion
- Number of components in report
- Parallel component execution
- Template rendering
- Success/failure statistics
- Total execution duration

**Example logs:**
```
INFO: Starting report execution for report_id='dashboard'
INFO: Report loaded: 'Executive Dashboard' with 5 component(s)
DEBUG: Executing report components in parallel
INFO: Component execution completed: 5/5 successful
INFO: Report execution completed: success=5, failures=0, total_duration=2.34s
```

### 4. Component Executor (`src/queryhub/services/component_executor.py`)

**Added logging for:**
- Individual component execution start/end
- Provider initialization and caching
- Query execution attempts
- Retry policies and timeouts
- Rendering completion
- Row counts and execution duration

**Example logs:**
```
INFO: Starting execution of component: sales_data (Sales Summary)
DEBUG: Component details: provider_id=postgres_db, timeout=30.0, retries=3
DEBUG: Using cached provider: postgres_db
DEBUG: Executing query for component: sales_data
INFO: Component 'sales_data' query completed successfully (attempts=1, rows=150)
INFO: Component 'sales_data' execution completed in 1.23s (success=True)
```

### 5. Email Client (`src/queryhub/email/client.py`)

**Added logging for:**
- Email message building
- Recipient resolution (to, cc, bcc)
- Subject line formatting
- SMTP connection details
- Message transmission success/failure

**Example logs:**
```
INFO: Preparing to send email for report: Daily Sales Report
DEBUG: Resolving email recipients for report: daily_sales
DEBUG: Recipients resolved: to=3, cc=1, bcc=0
DEBUG: Email from: reports@company.com, to: ['user@company.com']
INFO: Sending email via SMTP (server=smtp.gmail.com:587)
DEBUG: Connecting to SMTP server: smtp.gmail.com:587 (TLS=False, STARTTLS=True)
INFO: Email sent successfully
```

### 6. Retry Mechanism (`src/queryhub/core/retry.py`)

**Enhanced logging for:**
- Retry operation start with policy details
- Individual attempt execution
- Failure details with exception type
- Retry delays and backoff calculation
- Non-retryable errors
- Final success or failure

**Example logs:**
```
DEBUG: Starting retry operation (max_attempts=3, backoff=1.50s)
DEBUG: Executing attempt 1/3
WARNING: Attempt 1/3 failed: ConnectionError: Connection refused. Retrying in 1.50s
DEBUG: Executing attempt 2/3
INFO: Operation succeeded on attempt 2/3
```

### 7. Provider Base Class (`src/queryhub/providers/base_query_provider.py`)

**Added logging for:**
- Provider initialization with type and ID

**Example logs:**
```
DEBUG: Initialized provider: azure_adx (type=adx)
```

### 8. Specific Provider Implementations

#### CSV Provider (`src/queryhub/providers/generic/resources/csv.py`)

**Added logging for:**
- Root path initialization
- CSV file reading
- Row counts before and after filtering
- File not found errors

**Example logs:**
```
INFO: CSV provider initialized: root_path=/data/csv
DEBUG: Reading CSV file: /data/csv/sales.csv
DEBUG: CSV file loaded: 1000 row(s)
DEBUG: Applying 2 filter(s) to CSV data
DEBUG: Filters applied: 250 row(s) remaining
```

#### Azure Data Explorer Provider (`src/queryhub/providers/azure/resources/adx.py`)

**Added logging for:**
- Cluster and database initialization
- ADX client creation
- Credential retrieval
- Query execution with truncated query text
- Row counts and execution time
- Connection cleanup

**Example logs:**
```
INFO: ADX provider initialized: cluster=https://cluster.region.kusto.windows.net, database=analytics
DEBUG: Creating ADX client for cluster: https://cluster.region.kusto.windows.net
DEBUG: Retrieving Azure credentials: azure_default
DEBUG: Establishing authenticated connection to ADX
INFO: ADX client created successfully
DEBUG: Executing ADX query on database: analytics
DEBUG: Query text (first 100 chars): Users | where Timestamp > ago(7d) | summarize count() by Country
DEBUG: ADX query completed: 45 row(s), execution_time=0:00:01.234567
```

## Log Output Format

The default log format includes:
```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

**Example:**
```
2025-11-15 14:30:45,123 [INFO] queryhub.cli: Starting QueryHub report execution for report_id='daily_sales'
2025-11-15 14:30:45,456 [DEBUG] queryhub.config.loader: Loading provider configurations
2025-11-15 14:30:45,789 [INFO] queryhub.services.executor: Report loaded: 'Daily Sales Report' with 3 component(s)
```

## Controlling Log Verbosity

Users can control logging verbosity using the `--verbose` or `-v` flag:

```bash
# Normal logging (INFO level)
queryhub run-report daily_sales

# Verbose logging (DEBUG level)
queryhub run-report daily_sales --verbose
```

## Benefits

1. **Progress Visibility**: Users can see exactly what the application is doing at each step
2. **Debugging**: Detailed DEBUG logs help troubleshoot issues
3. **Performance Tracking**: Execution times and row counts are logged
4. **Error Context**: Failures include detailed context about what went wrong
5. **Audit Trail**: Complete record of operations for compliance and analysis
6. **Production Monitoring**: Logs can be forwarded to monitoring systems for alerting

## Best Practices Followed

- ✅ Used structured logging with consistent formatting
- ✅ Included relevant context in log messages (IDs, counts, durations)
- ✅ Separated INFO (user-facing) from DEBUG (technical details)
- ✅ Logged both successes and failures
- ✅ Used appropriate log levels consistently
- ✅ Avoided logging sensitive information (passwords, credentials)
- ✅ Truncated potentially large data (query text limited to 100 chars)
- ✅ Provided execution metrics (duration, row counts, success rates)

## Future Enhancements

Potential improvements for future consideration:

1. **Structured Logging**: Add JSON-formatted logs for machine parsing
2. **Correlation IDs**: Add request IDs to track operations across components
3. **Performance Metrics**: Add more detailed performance profiling
4. **Log Sampling**: Sample high-frequency DEBUG logs in production
5. **External Logging**: Integration with external logging services (CloudWatch, Azure Monitor, etc.)
