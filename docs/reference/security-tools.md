# Security Tools

QueryHub uses two primary security tools to maintain code quality and security:

## Bandit - Security Linting

[Bandit](https://bandit.readthedocs.io/) scans Python code for common security issues.

### Usage

```bash
# Run security checks
make security

# Or run directly
bandit -r src/ -c .bandit
```

### Configuration

Bandit is configured in `.bandit`:
- Excludes test directories
- Skips B101 (assert_used) - common in type guards
- Medium severity and confidence threshold

### Suppressing False Positives

Add `# nosec` comments to suppress specific warnings:

```python
PASSWORD = "token"  # nosec B105 - enum value, not a password
```

## Safety - Dependency Vulnerability Scanner

[Safety](https://docs.safetycli.com/) checks project dependencies against known security vulnerabilities.

### Usage

```bash
# Check for vulnerable dependencies
make safety-check

# Or run directly
safety scan --policy-file .safety-policy.yml
```

### Configuration

Safety is configured in `.safety-policy.yml`:
- Ignores vulnerabilities below medium severity
- Excludes system-wide packages not part of QueryHub
- Configurable ignore list for specific CVEs

## CI Integration

Both tools run automatically in GitHub Actions on every push and pull request:

1. **Bandit** - Fails the build if high/medium severity issues are found
2. **Safety** - Continues on error (advisory only) but reports vulnerabilities

## Best Practices

### Code Security (Bandit)

- ✅ Avoid hardcoded passwords/secrets
- ✅ Use parameterized SQL queries
- ✅ Validate file paths before operations
- ✅ Don't use `eval()` or `exec()` with user input
- ✅ Use secure random generators (`secrets` module)

### Dependency Security (Safety)

- ✅ Keep dependencies up-to-date
- ✅ Review vulnerability reports regularly
- ✅ Pin dependency versions in production
- ✅ Use virtual environments to isolate packages
- ✅ Remove unused dependencies

## Updating Dependencies

When Safety reports vulnerabilities:

```bash
# Check which package is affected
safety scan --policy-file .safety-policy.yml

# Update the specific package
uv add <package-name>@latest

# Or update all packages
uv sync --upgrade

# Update lockfile
uv lock --upgrade
```

## Adding Exceptions

### Bandit Exceptions

For false positives, add inline comments:

```python
# nosec B404 - subprocess usage is safe here
subprocess.run(["ls", directory], check=True)
```

Or update `.bandit` to skip specific tests globally.

### Safety Exceptions

Add to `.safety-policy.yml`:

```yaml
security:
  ignore-vulnerabilities:
    12345:
      reason: "False positive - not exploitable in our context"
      expires: "2025-12-31"
```

## References

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://docs.safetycli.com/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
