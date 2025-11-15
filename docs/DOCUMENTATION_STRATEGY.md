# Documentation Strategy

This document explains how QueryHub documentation is organized to minimize maintenance burden.

## Principles

### 1. Single Source of Truth (SSOT)
- **One canonical place** for each piece of information
- Other documents **link** to the source, never duplicate
- When code/config changes, only update one place

### 2. Reference Real Files
- Example configs reference actual working files in `config/`
- Don't copy-paste examples into docs
- Use relative links: `[See example](../../config/reports/daily_sales_report/)`

### 3. Layered Documentation
```
README.md              → Overview, quick start, links to detailed docs
├─ docs/guides/        → Step-by-step tutorials (getting-started.md)
└─ docs/reference/     → Detailed specifications (cli.md, architecture.md)
```

## Documentation Structure

### README.md (Entry Point)
**Purpose:** First impression, quick orientation
**Contains:**
- Problem statement
- Key features (brief)
- Quick start (5 minutes to first result)
- Links to detailed guides
- Examples with live HTML reports

**Rules:**
- ✅ Keep under 500 lines
- ✅ Link to detailed docs, don't duplicate
- ✅ Show working example using actual `config/` folder
- ❌ Don't include full configuration examples
- ❌ Don't document every CLI flag

### docs/guides/ (Tutorials)

#### getting-started.md
**Purpose:** Complete walkthrough for new users
**Contains:**
- Installation
- Configuration structure explanation
- First report creation
- Running and testing

**Rules:**
- ✅ Reference actual files: `config/reports/daily_sales_report/`
- ✅ Link to CLI reference for command options
- ❌ Don't duplicate CLI syntax
- ❌ Don't copy full config examples

**Example:**
```markdown
## Configuration Structure
See the complete working example in [`config/`](../../config/):
- SMTP: [`config/smtp/default.yaml`](../../config/smtp/default.yaml)
- Providers: [`config/providers/`](../../config/providers/)
- Reports: [`config/reports/daily_sales_report/`](../../config/reports/daily_sales_report/)
```

### docs/reference/ (Specifications)

#### cli.md (Single Source for CLI)
**Purpose:** Complete CLI command reference
**Contains:**
- All commands with full syntax
- All flags and options
- Examples

**Rules:**
- ✅ This is the ONLY place CLI syntax is documented
- ✅ Keep up-to-date with actual CLI code
- ✅ Other docs link here: "See [CLI Reference](../reference/cli.md)"

#### Other References
- `architecture.md` - System design
- `html-visualizations.md` - Visualization types
- `security-tools.md` - Security scanning

## Maintenance Workflow

### When Code Changes

1. **CLI changes** → Update `docs/reference/cli.md` only
2. **Config structure changes** → Update working `config/` files + README structure diagram
3. **New feature** → Add to README features list (1-2 lines) + detailed guide

### When to Create New Docs

**Create a new guide when:**
- ✅ Tutorial requires 10+ steps
- ✅ Topic is specific (e.g., "Azure Authentication")
- ✅ Content is evergreen (rarely changes)

**Don't create a doc for:**
- ❌ CLI commands (put in cli.md)
- ❌ Config examples (use actual files)
- ❌ Quick tips (put in README)

## Testing Documentation

### Automated Checks
```bash
# Check all internal links work
markdown-link-check docs/**/*.md

# Check code examples are valid
pytest docs/ --doctest-modules
```

### Manual Review Checklist
- [ ] All CLI examples use current syntax from `cli.md`
- [ ] Config examples reference actual files in `config/`
- [ ] No duplicate explanations (check SSOT principle)
- [ ] Links work: `../../config/` paths are correct

## Examples of Good vs Bad Documentation

### ❌ Bad (Duplicates Information)
```markdown
<!-- In getting-started.md -->
## Running Reports
Use the run-report command:
- `--config-dir`: Config directory
- `--templates-dir`: Templates directory
- `--output-html`: Output file
[Full list of options...]
```

### ✅ Good (Links to SSOT)
```markdown
<!-- In getting-started.md -->
## Running Reports
Run your first report:
\`\`\`bash
queryhub run-report config/reports/my_report
\`\`\`

For all command options, see [CLI Reference](../reference/cli.md).
```

### ❌ Bad (Duplicates Config)
```markdown
<!-- In multiple docs -->
Create `config/smtp.yaml`:
\`\`\`yaml
host: smtp.gmail.com
port: 587
...
\`\`\`
```

### ✅ Good (References Real File)
```markdown
Configure SMTP by editing [`config/smtp/default.yaml`](../../config/smtp/default.yaml).
See the default configuration for all available options.
```

## Doc File Ownership

| File | Owner | Update When |
|------|-------|-------------|
| README.md | Project lead | Features, structure changes |
| docs/guides/getting-started.md | Docs team | Onboarding flow changes |
| docs/reference/cli.md | CLI developer | CLI code changes |
| config/* | Everyone | Working examples |

## Migration Plan

### Phase 1: Consolidate (Done)
- ✅ Move templates to `config/templates/`
- ✅ Move SMTP to `config/smtp/`
- ✅ Update CLI to auto-discover

### Phase 2: Simplify Documentation
- [ ] Audit all docs for duplicates
- [ ] Replace config examples with links to `config/`
- [ ] Centralize CLI syntax in cli.md
- [ ] Add link checks to CI

### Phase 3: Automate
- [ ] Generate CLI docs from code docstrings
- [ ] Auto-test code examples in docs
- [ ] Add "last updated" dates

## Resources

- [Write the Docs - Documentation Principles](https://www.writethedocs.org/)
- [Divio Documentation System](https://documentation.divio.com/)
- [Keep a Changelog](https://keepachangelog.com/)
