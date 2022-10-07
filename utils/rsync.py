import os
import subprocess
import typing as t


class RsyncOptions:
    def __init__(self, root: str, delete_from_destination: bool, show_progress: bool = False,
                 dry_run: bool = False):
        SSH_CMD = 'ssh -p 15822 -i /home/fabian/.ssh/id_rsa'
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
        self.OPTS = ['-e', SSH_CMD, *INFO_OPTS, *BACKUP_OPTS, *ARCHIVE_OPTS]
        self.HOST = 'prg-backup@biberbunker.fineshift.de'
        self.MODULE = 'NetBackup'
        self.ROOT = os.path.join('/prg-srv-001', root)


def run_rsync_without_delete(source: str, destination_root: str, destination: str, dry_run: bool = False) -> \
    t.List[str]:
    opt = RsyncOptions(root=destination_root, delete_from_destination=False)
    cmd = [
        'rsync', *opt.OPTS,
        '--', source,
        f"{opt.HOST}::{opt.MODULE}{opt.ROOT}/{destination}"
    ]
    if not dry_run:
        print(f"Running {cmd}")
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_incremental(source: str, destination_root: str, destination: str, backup_dir: str,
                                 dry_run: bool = False) -> t.List[str]:
    opt = RsyncOptions(root=destination_root, delete_from_destination=True)
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


def run_rsync_backup_with_hardlinks(source: str, destination_root: str, new_backup: str,
                                    old_backup_dirs: t.List[str],
                                    dry_run: bool = False) -> t.List[str]:
    opt = RsyncOptions(root=destination_root, delete_from_destination=True)
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
