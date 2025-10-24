# Doco

<span style="font-weight: bold">doco</span> (<span style="font-weight: bold">do</span>cker <span style="font-weight: bold">co</span>mpose tool) is a command line tool
for working with <span style="font-style: italic">docker compose</span> projects
(pretty-printing status, creating backups using rsync, batch commands and more).

**Usage**:

```console
$ doco [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--version`: Show version information and exit.
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `s`: Print status of projects.
* `u`: Start projects.
* `d`: Shutdown projects.
* `r`: Restart projects.
* `l`: Print logs of projects.
* `backups`: Create, restore, download or list backups.

## `doco s`

Print status of projects.

**Usage**:

```console
$ doco s [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `--path`: Print path of compose file.
* `-P, --profiles`: Output profile names of services.
* `-b, --build`: Output build context and arguments.
* `-e, --envs`: List environment variables.
* `-v, --volumes`: List volumes (use -vv to also list content).
* `-V, --verbose`: Like -pPbev (use -VV for -pPbevv).
* `--no-show-profiles`: Don&#x27;t print (enabled) profile names for projects.
* `-R, --right`: Right-align variable names.
* `-Z, --zebra`: Alternate row colors in tables.
* `--help`: Show this message and exit.

## `doco u`

Start projects.

**Usage**:

```console
$ doco u [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `--pull`: Pull images before running.
* `-l, --log`: Also show logs.
* `-t, --timestamps`: Show timestamps in logs.
* `--no-build`: Don&#x27;t build images before running.
* `--no-remove-orphans`: Keep orphans.
* `-n, --dry-run`: Do not actually start anything, only show what would be done.
* `--help`: Show this message and exit.

## `doco d`

Shutdown projects.

**Usage**:

```console
$ doco d [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `-v, --remove-volumes`: Remove volumes (implies -f / --force).
* `--no-remove-orphans`: Keep orphans.
* `-f, --force`: Force calling down even if not running.
* `-n, --dry-run`: Do not actually stop anything, only show what would be done.
* `--help`: Show this message and exit.

## `doco r`

Restart projects. This is like <span style="font-style: italic">down</span> and <span style="font-style: italic">up</span> in one command.

**Usage**:

```console
$ doco r [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `-v, --remove-volumes`: Remove volumes (implies -f / --force).
* `--no-remove-orphans`: Keep orphans.
* `-f, --force`: Force calling down even if not running.
* `--pull`: Pull images before running.
* `-l, --log`: Also show logs.
* `-t, --timestamps`: Show timestamps in logs.
* `--no-build`: Don&#x27;t build images before running.
* `-n, --dry-run`: Do not actually stop anything, only show what would be done.
* `--help`: Show this message and exit.

## `doco l`

Print logs of projects.

**Usage**:

```console
$ doco l [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `-t, --timestamps`: Show timestamps.
* `-q, --no-follow`: Quit right after printing logs.
* `--help`: Show this message and exit.

## `doco backups`

Create, restore, download or list backups.

**Usage**:

```console
$ doco backups [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `create`: Backup projects.
* `restore`: Restore project backups.
* `raw`: Manage backups (independently of <span style="font-style: italic">docker...</span>

### `doco backups create`

Backup projects.

**Usage**:

```console
$ doco backups create [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `-e, --exclude-project-dir`: Exclude project directory.
* `-r, --include-ro`: Also consider read-only volumes.
* `-v, --volume TEXT`: Regex for volume selection, can be specified multiple times. Use -v <span style="color: #808000; text-decoration-color: #808000; font-weight: bold">&#x27;(?!)&#x27;</span> to exclude all volumes. Use -v <span style="color: #808000; text-decoration-color: #808000; font-weight: bold">^/path/</span> to only allow specified paths. <span style="color: #7f7f7f; text-decoration-color: #7f7f7f">[default: (exclude many system directories)]</span>
* `--live`: Do not stop the services before backup.
* `-b, --backup TEXT`: Specify backup name.
* `--deep`: Use deep instead of flat root dir names (e.g. home/john instead of home__john).
* `--progress`: Show rsync progress.
* `-V, --verbose`: Print more details.
* `-n, --dry-run`: Do not actually backup, only show what would be done.
* `--skip-root-check`: Do not cancel when not run with root privileges.
* `--help`: Show this message and exit.

### `doco backups restore`

Restore project backups.

**Usage**:

```console
$ doco backups restore [OPTIONS] [PROJECTS]...
```

**Arguments**:

* `[PROJECTS]...`: Compose files and/or directories containing a [docker-]compose.y[a]ml.  [default: (stdin or current directory)]

**Options**:

* `-s, --service TEXT`: Select services (comma-separated or multiple -s arguments).
* `-p, --profile TEXT`: Enable specific profiles (comma-separated or multiple -p arguments).
* `-a, --all`: Select all profiles.
* `--running`: Consider only projects with at least one running or restarting service.
* `--name TEXT`: Override project name. Using directory name if not given.
* `-l, --list`: List backups instead of restoring a backup.
* `-b, --backup TEXT`: Backup index or name.  [default: 0]
* `--progress`: Show rsync progress.
* `-V, --verbose`: Print more details.
* `-n, --dry-run`: Do not actually restore a backup, only show what would be done.
* `--skip-root-check`: Do not cancel when not run with root privileges.
* `--help`: Show this message and exit.

### `doco backups raw`

Manage backups (independently of <span style="font-style: italic">docker compose</span>).

**Usage**:

```console
$ doco backups raw [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-w, --workdir DIRECTORY`: Change working directory.  [default: .]
* `-r, --root TEXT`: Change root.
* `--help`: Show this message and exit.

**Commands**:

* `ls`: List backups.
* `download`: Download a backup for local analysis.
* `create`: Backup files and directories.
* `restore`: Restore a backup.

#### `doco backups raw ls`

List backups.

Note that the order of backups is not guaranteed between backups created within the same second.

**Usage**:

```console
$ doco backups raw ls [OPTIONS] [PROJECT]
```

**Arguments**:

* `[PROJECT]`: Project to list backups from. Listing projects if not given.

**Options**:

* `--progress`: Show rsync progress.
* `-V, --verbose`: Print more details.
* `--help`: Show this message and exit.

#### `doco backups raw download`

Download a backup for local analysis.

**Usage**:

```console
$ doco backups raw download [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: Source project to retrieve backups from.  [required]

**Options**:

* `-b, --backup TEXT`: Backup index or name.  [default: 0]
* `-d, --destination DIRECTORY`: Destination (not relative to --workdir but to the caller&#x27;s CWD), defaults to --project within --workdir.
* `--progress`: Show rsync progress.
* `-V, --verbose`: Print more details.
* `-n, --dry-run`: Do not actually download, only show what would be done.
* `--skip-root-check`: Do not cancel when not run with root privileges.
* `--help`: Show this message and exit.

#### `doco backups raw create`

Backup files and directories.

**Usage**:

```console
$ doco backups raw create [OPTIONS] PROJECT PATHS...
```

**Arguments**:

* `PROJECT`: Target project to write backups to.  [required]
* `PATHS...`: Paths to backup (not relative to --workdir but to the caller&#x27;s CWD).  [required]

**Options**:

* `-b, --backup TEXT`: Specify backup name.
* `--deep`: Use deep instead of flat root dir names (e.g. home/john instead of home__john).
* `--incremental`: Use incremental backup strategy with a single directory, instead of having separate self-contained and hard-linked directories.
* `--incremental-backup TEXT`: Specify incremental backup directory name (for changed and removed files).
* `--progress`: Show rsync progress.
* `-V, --verbose`: Print more details.
* `-n, --dry-run`: Do not actually backup, only show what would be done.
* `--skip-root-check`: Do not cancel when not run with root privileges.
* `--help`: Show this message and exit.

#### `doco backups raw restore`

Restore a backup.

**Usage**:

```console
$ doco backups raw restore [OPTIONS] PROJECT
```

**Arguments**:

* `PROJECT`: Source project to retrieve backups from.  [required]

**Options**:

* `-b, --backup TEXT`: Backup index or name.  [default: 0]
* `--progress`: Show rsync progress.
* `-V, --verbose`: Print more details.
* `-n, --dry-run`: Do not actually restore a backup, only show what would be done.
* `--skip-root-check`: Do not cancel when not run with root privileges.
* `--help`: Show this message and exit.
