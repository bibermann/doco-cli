import json
import os
import subprocess
import typing as t

import dotenv
import yaml


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


def load_env_file():
    return dotenv.dotenv_values('.env')


def load_compose_config(cwd: str, file: str):
    result = subprocess.run(
        ['docker', 'compose', '-f', file, 'config'],
        cwd=cwd,
        capture_output=True,
        encoding='utf-8',
        universal_newlines=True,
        check=True,
    )
    return yaml.safe_load(result.stdout)


def load_compose_ps(cwd: str, file: str):
    result = subprocess.run(
        ['docker', 'compose', '-f', file, 'ps', '--format', 'json'],
        cwd=cwd,
        capture_output=True,
        encoding='utf-8',
        universal_newlines=True,
        check=True,
    )
    return json.loads(result.stdout)


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


def run_compose(compose_dir, compose_file, command: t.List[str], dry_run: bool = False,
                cancelable: bool = False):
    cmd = [
        'docker', 'compose', '-f', compose_file,
        *command,
    ]
    if not dry_run:
        print(f"Running {cmd} in {compose_dir}")
        try:
            subprocess.run(cmd, cwd=compose_dir, check=True)
        except KeyboardInterrupt:
            if not cancelable:
                raise

    return cmd


def relative_path_if_below(path: str) -> str:
    path = os.path.normpath(path)
    relpath = os.path.relpath(path)
    if relpath.startswith('../') or os.getcwd() == '/':
        return os.path.abspath(path)
    else:
        if not relpath == '.' and not relpath.startswith('./') and not relpath.startswith('/'):
            return './' + relpath
        else:
            return relpath


def find_compose_projects(paths: t.Iterable[str]) -> t.Generator[None, t.Tuple[str, str], None]:
    for project in paths:
        compose_dir = None
        compose_file = None
        if os.path.isfile(project) and 'docker-compose' in project and (
            project.endswith('.yml') or project.endswith('.yaml')):
            compose_dir, compose_file = os.path.split(project)
            if compose_dir == '':
                compose_dir = '.'
        if compose_dir is None or compose_file is None:
            for file in ['docker-compose.yml', 'docker-compose.yaml']:
                if os.path.exists(os.path.join(project, file)):
                    compose_dir, compose_file = project, file
                    break
        if compose_dir is None or compose_file is None:
            continue

        compose_dir = relative_path_if_below(compose_dir)
        yield compose_dir, compose_file
