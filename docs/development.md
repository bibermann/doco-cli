# Doco development

## Setup

Requirements:
- `poetry`
- `pyenv`

```bash
# Deactivate possibly activated venv
source deactivate || true

# Create virtual environment
pyenv install -s
poetry env use $(pyenv which python)
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

## Run doco

To run doco without installing it:
```bash
poetry run doco -h
```

## Run pre-commit manually

```bash
poetry run pre-commit run -a
```
