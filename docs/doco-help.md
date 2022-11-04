# Doco `--help`

## doco

doco (docker compose tool) is a command line tool for working with docker  
compose projects (pretty-printing status, creating backups using rsync, batch  
commands and more).

```
 Usage: doco [OPTIONS] COMMAND [ARGS]...  

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --version                       Show version information and exit.           │
│ --install-completion            Install completion for the current shell.    │
│ --show-completion               Show completion for the current shell, to    │
│                                 copy it or customize the installation.       │
│ --help                -h        Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ s          Print status of projects.                                         │
│ u          Start projects.                                                   │
│ d          Shutdown projects.                                                │
│ r          Restart projects. This is like down and up in one command.        │
│ l          Print logs of projects.                                           │
│ backups    Create, restore, download or list backups.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### doco s

Print status of projects.

```
 Usage: doco s [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running            Consider only projects with at least one running or     │
│                      restarting service.                                     │
│ --help     -h        Show this message and exit.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Content detail Options ─────────────────────────────────────────────────────╮
│ --path     -p               Print path of compose file.                      │
│ --build    -b               Output build context and arguments.              │
│ --envs     -e               List environment variables.                      │
│ --volumes  -v      INTEGER  List volumes (use -vv to also list content).     │
│                             [default: 0]                                     │
│ --all      -a      INTEGER  Like -pbev (use -aa for -pbevv). [default: 0]    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Formatting Options ─────────────────────────────────────────────────────────╮
│ --right          Right-align variable names.                                 │
│ --zebra          Alternate row colors in tables.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### doco u

Start projects.

```
 Usage: doco u [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running            Consider only projects with at least one running or     │
│                      restarting service.                                     │
│ --dry-run  -n        Do not actually start anything, only show what would be │
│                      done.                                                   │
│ --pull     -p        Pull images before running.                             │
│ --log      -l        Also show logs.                                         │
│ --help     -h        Show this message and exit.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### doco d

Shutdown projects.

```
 Usage: doco d [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running                      Consider only projects with at least one      │
│                                running or restarting service.                │
│ --remove-volumes     -v        Remove volumes (implies -f / --force).        │
│ --no-remove-orphans  -k        Keep orphans.                                 │
│ --force              -f        Force calling down even if not running.       │
│ --dry-run            -n        Do not actually stop anything, only show what │
│                                would be done.                                │
│ --help               -h        Show this message and exit.                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### doco r

Restart projects. This is like down and up in one command.

```
 Usage: doco r [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running                      Consider only projects with at least one      │
│                                running or restarting service.                │
│ --remove-volumes     -v        Remove volumes (implies -f / --force).        │
│ --no-remove-orphans  -k        Keep orphans.                                 │
│ --force              -f        Force calling down even if not running.       │
│ --pull               -p        Pull images before running.                   │
│ --log                -l        Also show logs.                               │
│ --dry-run            -n        Do not actually stop anything, only show what │
│                                would be done.                                │
│ --help               -h        Show this message and exit.                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### doco l

Print logs of projects.

```
 Usage: doco l [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running              Consider only projects with at least one running or   │
│                        restarting service.                                   │
│ --no-follow  -q        Quit right after printing logs.                       │
│ --help       -h        Show this message and exit.                           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### doco backups

Create, restore, download or list backups.

```
 Usage: doco backups [OPTIONS] COMMAND [ARGS]...  

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ create      Backup projects.                                                 │
│ restore     Restore project backups.                                         │
│ raw         Manage backups (independently of docker compose).                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### doco backups create

Backup projects.

```
 Usage: doco backups create [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running                            Consider only projects with at least    │
│                                      one running or restarting service.      │
│ --exclude-project-dir  -e            Exclude project directory.              │
│ --include-ro           -r            Also consider read-only volumes.        │
│ --volume               -v      TEXT  Regex for volume selection, can be      │
│                                      specified multiple times. Use -v '(?!)' │
│                                      to exclude all volumes. Use -v ^/path/  │
│                                      to only allow specified paths.          │
│                                      [default: (exclude many system          │
│                                      directories)]                           │
│ --live                               Do not stop the services before backup. │
│ --verbose                            Print more details if --dry-run.        │
│ --dry-run              -n            Do not actually backup, only show what  │
│                                      would be done.                          │
│ --help                 -h            Show this message and exit.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### doco backups restore

Restore project backups.

```
 Usage: doco backups restore [OPTIONS] [PROJECTS]...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   projects      [PROJECTS]...  Compose files and/or directories containing a │
│                                docker-compose.y[a]ml.                        │
│                                [default: (stdin or current directory)]       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --running                Consider only projects with at least one running or │
│                          restarting service.                                 │
│ --name             TEXT  Override project name. Using directory name if not  │
│                          given.                                              │
│                          [default: None]                                     │
│ --list     -l            List backups instead of restoring a backup.         │
│ --backup   -b      TEXT  Backup index or name. [default: 0]                  │
│ --verbose                Print more details if --dry-run.                    │
│ --dry-run  -n            Do not actually restore a backup, only show what    │
│                          would be done.                                      │
│ --help     -h            Show this message and exit.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### doco backups raw

Manage backups (independently of docker compose).

```
 Usage: doco backups raw [OPTIONS] COMMAND [ARGS]...  

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --workdir  -w      DIRECTORY  Change working directory. [default: .]         │
│ --root     -r      TEXT       Change root. [default: None]                   │
│ --help     -h                 Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ ls              List backups.                                                │
│ download        Download a backup for local analysis.                        │
│ create          Backup files and directories.                                │
│ restore         Restore a backup.                                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### doco backups raw ls

List backups.

```
 Usage: doco backups raw ls [OPTIONS] [PROJECT]  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   project      [PROJECT]  Project to list backups from. Listing projects if  │
│                           not given.                                         │
│                           [default: None]                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### doco backups raw download

Download a backup for local analysis.

```
 Usage: doco backups raw download [OPTIONS] PROJECT  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    project      TEXT  Source project to retrieve backups from.             │
│                         [default: None]                                      │
│                         [required]                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --backup       -b      TEXT       Backup index or name. [default: 0]         │
│ --destination  -d      DIRECTORY  Destination (not relative to --workdir but │
│                                   to the caller's CWD), defaults to          │
│                                   --project within --workdir.                │
│                                   [default: None]                            │
│ --dry-run      -n                 Do not actually download, only show what   │
│                                   would be done.                             │
│ --help         -h                 Show this message and exit.                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### doco backups raw create

Backup files and directories.

```
 Usage: doco backups raw create [OPTIONS] PROJECT PATHS...  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    project      TEXT      Target project to write backups to.              │
│                             [default: None]                                  │
│                             [required]                                       │
│ *    paths        PATHS...  Paths to backup (not relative to --workdir but   │
│                             to the caller's CWD).                            │
│                             [required]                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --verbose            Print more details if --dry-run.                        │
│ --dry-run  -n        Do not actually backup, only show what would be done.   │
│ --help     -h        Show this message and exit.                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

##### doco backups raw restore

Restore a backup.

```
 Usage: doco backups raw restore [OPTIONS] PROJECT  

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    project      TEXT  Source project to retrieve backups from.             │
│                         [default: None]                                      │
│                         [required]                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --backup   -b      TEXT  Backup index or name. [default: 0]                  │
│ --verbose                Print more details if --dry-run.                    │
│ --dry-run  -n            Do not actually restore a backup, only show what    │
│                          would be done.                                      │
│ --help     -h            Show this message and exit.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```
