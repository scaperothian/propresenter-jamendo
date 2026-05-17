# ProPresenter Jamendo

ProPresenter integration with Jamendo royalty-free music.

## Requirements

- Python >= 3.12
- [Poetry](https://python-poetry.org/) 2.x

## Setup

```bash
# Create and activate the virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
poetry install
```

## Development

All feature work must be done in a feature branch — never directly on `main`.

```bash
# Create a feature branch
git checkout -b feature/my-feature

# ... make changes ...

# Run tests before committing
pytest
```

## Running Tests

```bash
source venv/bin/activate
pytest
```

## Project Structure

```
propresenter-jamendo/
├── src/
│   └── propresenter_jamendo/   # Main package
├── tests/                      # Pytest test suite
├── venv/                       # Local virtual environment (not committed)
├── pyproject.toml              # Poetry dependency declarations
├── poetry.toml                 # Poetry local config (disables internal venv)
└── CLAUDE.md                   # AI assistant instructions
```
