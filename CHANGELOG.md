# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Support new `compose.yaml` default name.
- Add option `-s, --service` to select compose services.
- Add option `-p, --profile` to select compose profiles.
- Add option `-a, --all` to select all compose profiles.
- Add option `-t, --timestamps` to show timestamps in logs.
- Add option `--deep` for creating backups to use deep instead of flat root dir names.
- Introduce incremental backup strategy for raw backups
    with new options `--incremental` and `--incremental-backup`.
- Add option `--skip-root-check` for create/download/restore (raw) backups.
- Add option `--show-progress` for file transfers (uses `--info=progress2` for rsync operations).
- Add/use option `-V, --verbose` for rsync operations.
- Add `--create-schema` option to write a doco config JSON schema file.

### Changed
- Verbose option changed from `-a, --all` to `-V, --verbose`.
- Render status aligned when no details are requested.

## [2.2.2] -- 2024-10-20
### Fixed
- Highlight and don't back up non-existing bind-mount volumes.
- Render commands more copy-paste-friendly (w/o borders and w/o hard linebreaks).
- Support new `docker compose ps --json` format.

## [2.2.1] -- 2022-11-27
### Fixed
- Fix UID/GID was not changed for all relevant directories.

## [2.2.0] -- 2022-11-26
### Added
- Introduce `.backup.structure` and `.backup.restore_structure` configuration
    to allow changing UID/GID for the backup directory structure and configuration files.

## [2.1.0] -- 2022-11-26
### Added
- Introduce `.backup.rsync.args` configuration to specify args to forward to rsync.

### Deprecated
- Deprecate `.backup.rsync.rsh` configuration in favor of `.backup.rsync.args`.

## [2.0.0] -- 2022-11-25
### Added
- Support TOML config format.
- Support `DOCO_BACKUP_RSYNC_*` environment variables.
- Add option to show logs (in `up` and `restart` commands).
- Add option to pull images before running (in `up` and `restart` commands).
- Allow specifying backup item directory name.
- Add `--no-build` option (in up and restart commands).

### Changed
- Show command that gets executed more prominent with surrounding border.
- Follow logs by default (in `log` command).
- Don't imply `backup-` prefix when listing or specifying backup items.
- Display mapped volume name for named volumes.

### Fixed
- Fix shell completion for arguments.
- Allow empty module for rsync.
- Don't print stacktrace on docker/rsync process errors.
- Add `--remove-orphans` to `docker compose up` by default.

## [1.0.0] - 2021-10-30
### Added
- Publish first official version of Doco.

[Unreleased]: https://github.com/bibermann/doco-cli/compare/2.2.2...HEAD
[2.2.2]: https://github.com/bibermann/doco-cli/compare/2.2.1...2.2.2
[2.2.1]: https://github.com/bibermann/doco-cli/compare/2.2.0...2.2.1
[2.2.0]: https://github.com/bibermann/doco-cli/compare/2.1.0...2.2.0
[2.1.0]: https://github.com/bibermann/doco-cli/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/bibermann/doco-cli/compare/1.0.0...2.0.0
[1.0.0]: https://github.com/bibermann/doco-cli/releases/tag/1.0.0
