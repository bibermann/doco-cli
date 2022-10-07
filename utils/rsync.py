import os
import subprocess
import typing as t

import pydantic


class RsyncConfig(pydantic.BaseModel):
    rsh: t.Optional[str] = None
    host: str = ''
    module: str = ''
    root: str = '/'


class RsyncOptions:
    def __init__(
        self, config: RsyncConfig,
        delete_from_destination: bool, show_progress: bool = False,
        dry_run: bool = False
    ):
        if config.host == '' or config.module == '':
            exit("You need to configure rsync to do a backup.\n"
                 "Please see documentation for 'doco.config.json'. Exiting.")

        SSH_OPTS = ['-e', config.rsh] if config.rsh is not None else []
        INFO_OPTS = [
            '-h',
            *(['--info=progress2'] if show_progress else []),
        ]
        BACKUP_OPTS = [
            *(['--delete'] if delete_from_destination else []),
            # '--mkpath', # --mkpath supported only since 3.2.3
            '-z',
            *(['-n'] if dry_run else []),
        ]
        ARCHIVE_OPTS = [
            '-a',
            # '-N', # -N (--crtimes) supported only on OS X apparently
            '--numeric-ids'
        ]
        self.OPTS = [*SSH_OPTS, *INFO_OPTS, *BACKUP_OPTS, *ARCHIVE_OPTS]
        self.HOST = config.host
        self.MODULE = config.module
        self.ROOT = config.root


def run_rsync_without_delete(
    config: RsyncConfig, source: str, destination: str,
    dry_run: bool = False
) -> t.List[str]:
    opt = RsyncOptions(config=config, delete_from_destination=False)
    cmd = [
        'rsync', *opt.OPTS,
        '--', source,
        f"{opt.HOST}::{opt.MODULE}{opt.ROOT}/{destination}"
    ]
    if not dry_run:
        print(f"Running {cmd}")
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_incremental(
    config: RsyncConfig, source: str, destination: str, backup_dir: str,
    dry_run: bool = False
) -> t.List[str]:
    opt = RsyncOptions(config=config, delete_from_destination=True)
    cmd = [
        'rsync', *opt.OPTS,
        '--backup-dir', f"{opt.ROOT}/{backup_dir}",
        '--', source,
        f"{opt.HOST}::{opt.MODULE}{opt.ROOT}/{destination}"
    ]
    if not dry_run:
        print(f"Running {cmd}")
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_with_hardlinks(
    config: RsyncConfig,
    source: str, new_backup: str, old_backup_dirs: t.List[str],
    dry_run: bool = False
) -> t.List[str]:
    opt = RsyncOptions(config=config, delete_from_destination=True)
    for old_backup_dir in old_backup_dirs:
        opt.OPTS.extend(['--link-dest', f"{opt.ROOT}/{old_backup_dir}"])
    cmd = [
        'rsync', *opt.OPTS,
        '--', source,
        f"{opt.HOST}::{opt.MODULE}{opt.ROOT}/{new_backup}"
    ]
    if not dry_run:
        print(f"Running {cmd}")
        subprocess.run(cmd, check=True)
    return cmd
