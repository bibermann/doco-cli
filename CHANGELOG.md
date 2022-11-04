# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Support TOML config format.
- Support `DOCO_BACKUP_RSYNC_*` environment variables.
- Add option to show logs (in up and restart commands).
- Add option to pull images before running (in up and restart commands).

### Changed
- Show command that gets executed more prominent with surrounding border.
- Follow logs by default (in log command).

### Fixed
- Fix shell autocompletion for arguments.

## [1.0.0] - 2021-10-30
### Added
- Publish first official version of Doco.

[Unreleased]: https://github.com/bibermann/doco-cli/compare/1.0.0...HEAD
[1.0.0]: https://github.com/bibermann/doco-cli/releases/tag/1.0.0
