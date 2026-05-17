# CLAUDE.md — Project Conventions for AI Assistants

This file describes how work should be done in this repository. Follow these rules in every session.

## Git Workflow

- The default branch is `main`. **Never commit feature work directly to `main`.**
- All changes must be made in a feature branch:
  ```bash
  git checkout -b feature/<short-description>
  ```
- Merge to `main` only via a reviewed and tested PR (or explicit user instruction).
- Use descriptive commit messages in the imperative mood ("Add Jamendo search client").

## Testing

- **Run `pytest` immediately after every code change** to catch regressions.
- Tests live in `tests/`. Mirror the `src/` structure (e.g. `src/propresenter_jamendo/foo.py` → `tests/test_foo.py`).
- All new features must be accompanied by tests.
- Do not commit code that makes existing tests fail.

```bash
source venv/bin/activate
pytest
```

## Environment Management

### Virtual Environment

The project uses a **non-hidden `venv/` directory** (not `.venv/`) for the Python virtual environment.

```bash
# Create (first time only)
python3 -m venv venv

# Activate (every session)
source venv/bin/activate

# Deactivate when done
deactivate
```

The `venv/` directory is excluded from git (see `.gitignore`).

### Python Version

Python version is managed through the `venv/` directory. The interpreter baked into the venv at creation time determines the runtime Python version. To change the Python version, recreate the venv:

```bash
/path/to/target/python3 -m venv venv
```

#### VSCode Note

VSCode may not automatically pick up the `venv/` interpreter. If you see import errors or the wrong Python version in VSCode:

1. Open the Command Palette (`Cmd+Shift+P`)
2. Run **"Python: Select Interpreter"**
3. Choose `./venv/bin/python`

#### Python Version Mismatch Workaround

If you encounter a Python version mismatch error (e.g., Poetry or another tool conflicts with an existing `VIRTUALENV` environment variable), unset it:

```bash
unset VIRTUALENV
```

Then re-activate the venv normally.

### Dependency Management

Dependencies are declared in `pyproject.toml` and managed with [Poetry](https://python-poetry.org/).

`poetry.toml` sets `virtualenvs.create = false` so Poetry uses the **active venv** instead of creating its own. Always activate the venv before running Poetry commands:

```bash
source venv/bin/activate
poetry add <package>      # add a runtime dependency
poetry add --group dev <package>  # add a dev/test dependency
poetry install            # install all declared deps into active venv
```

### Critical Dependencies

| Package | Purpose |
|---------|---------|
| pytest  | Test runner |

Add new critical dependencies to this table when introduced.

## Project Structure

```
propresenter-jamendo/
├── src/
│   └── propresenter_jamendo/   # Main package
├── tests/                      # Pytest suite
├── venv/                       # Local Python environment (not in git)
├── pyproject.toml              # Dependency declarations (Poetry)
├── poetry.toml                 # Poetry local config
├── .gitignore                  # Python + venv gitignore
├── README.md
└── CLAUDE.md                   # This file
```

## Summary of Rules

1. Feature branches only — never work on `main`.
2. Run `pytest` after every change.
3. Always activate `venv/` before running Python or Poetry commands.
4. If Python version mismatch: `unset VIRTUALENV`.
5. If VSCode shows wrong interpreter: set it manually via "Python: Select Interpreter".
