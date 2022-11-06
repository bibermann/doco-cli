# Doco CLI

**doco** (**do**cker **co**mpose tool) is a command line tool
for working with [Docker Compose](https://docs.docker.com/compose/compose-file/) projects
(pretty-printing status, creating backups using rsync, batch commands and more).

[![Code style](https://github.com/bibermann/doco-cli/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/bibermann/doco-cli/actions/workflows/pre-commit.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI](https://img.shields.io/pypi/v/doco-cli)](https://pypi.org/project/doco-cli)

## Usage

Example calls:

- `doco s *`: Print pretty status of all _docker compose_ projects in the current directory.
- `doco s . -aa`: Print most detailled status of a _docker compose_ project (including variables and volumes).
- `doco r .`: Equivalent of `docker compose down --remove-orphans && docker compose up --build -d`.
- `doco backups create . --dry-run --verbose`: See what would be done to create a backup of a _docker compose_ project.

To explore all possibilities, run `doco -h` or see  [docs/doco-help.md](docs/doco-help.md).

## Installation

```bash
pipx install doco-cli
doco --install-completion
```

Or install from source, see [docs/installation.md](docs/installation.md).

## Configuration

To create a backup, you need to either create a `doco.config.toml` file,
a `doco.config.json` file
or set environment variables.

See [docs/configuration.md](docs/configuration.md).

## Development

To start developing, see [docs/development.md](docs/development.md).
