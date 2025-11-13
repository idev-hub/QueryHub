# QueryHub

QueryHub is an open-source automation platform that enables users to generate and distribute data reports via email based on predefined queries. It eliminates manual report generation by scheduling query execution and automating email delivery at specified intervals.

## Features (planned)
- Schedule SQL or API queries and deliver the results to stakeholders automatically.
- Manage delivery templates and recipient lists in configuration files.
- Track execution history, delivery status, and upcoming runs.

## Project structure
```
QueryHub/
├── .github/              # GitHub workflows and community health files
├── docs/                 # User and contributor documentation
├── examples/             # Sample configurations and runbooks
├── scripts/              # Utility scripts for local development
├── src/queryhub/         # Package source code
└── tests/                # Automated tests
```

## Getting started
```bash
git clone https://github.com/isasnovich/QueryHub.git
cd QueryHub
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run the default checks with:

```bash
ruff check
pytest
```

## Contributing
Please read `CONTRIBUTING.md` for guidelines on how to propose improvements or submit pull requests. By participating, you agree to follow the `CODE_OF_CONDUCT.md`.

## License
QueryHub is distributed under the terms of the MIT License (`LICENSE`).
