# Doco CLI

**doco** (**do**cker **co**mpose tool) is a command line tool for working with _docker compose_ projects
(pretty-printing status, creating backups using rsync, batch commands and more).

Example calls:

- `doco s *`: Print pretty status of all _docker compose_ projects in the current directory.
- `doco s . -aa`: Print most detailled status of a _docker compose_ project (including variables and volumes).
- `doco r .`: Equivalent of `docker compose down --remove-orphans && docker compose up --build -d`.
- `doco backups create . --dry-run`: See what would be done to create a backup of a _docker compose_ project.

To explore all possibilities, run `doco -h` or see  [docs/doco-help.md](docs/doco-help.md).

## Installation

```bash
pipx install doco-cli
doco --install-completion
```

Or install from source, see [docs/installation.md](docs/installation.md).

## Configuration

To create a backup, you need to create a `doco.config.json` file.

See [docs/configuration.md](docs/configuration.md).

## Development

To start developing, see [docs/development.md](docs/development.md).
