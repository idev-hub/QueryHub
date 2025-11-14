# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Migrated from pip to uv for dependency management
  - Updated all CI/CD workflows to use `astral-sh/setup-uv@v5`
  - Replaced `setuptools` with `hatchling` as build backend
  - Updated Makefile targets to use `uv sync` instead of `pip install`
  - Updated setup script and all documentation
  - See `docs/guides/uv-migration.md` for migration instructions

### Added
- Added `uv.lock` for deterministic dependency resolution
- Added `.python-version` file for Python version specification
- Added uv badge to README
- Added comprehensive uv migration guide
- Added security tools: Bandit and Safety
  - Bandit for security linting (detects common security issues)
  - Safety for dependency vulnerability scanning
  - Added configuration files: `.bandit` and `.safety-policy.yml`
  - Integrated both tools into CI/CD pipeline
  - Added `make security` and `make safety-check` targets
  - Added documentation in `docs/reference/security-tools.md`
- Added "How to add a new provider" section to README with detailed examples

### Fixed
- Suppressed false positive security warnings in credential type enums

### Documentation
- Updated README with uv installation instructions
- Updated all documentation to use uv instead of pip
- Added migration guide for existing contributors
- Enhanced security tools documentation
- Improved provider extension documentation
