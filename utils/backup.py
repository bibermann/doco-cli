import dataclasses
import os
import tempfile
import typing as t

import rich.tree

from utils.common import relative_path
from utils.common import relative_path_if_below
from utils.rich import format_cmd_line
from utils.rsync import RsyncConfig
from utils.rsync import run_rsync_backup_with_hardlinks
from utils.rsync import run_rsync_without_delete

LAST_BACKUP_DIR_FILENAME = '.last-backup-dir'


@dataclasses.dataclass
class BackupJob:
    display_source_path: str
    display_target_path: str
    relative_source_path: str
    relative_target_path: str
    rsync_source_path: str
    rsync_target_path: str
    is_dir: bool

    def __init__(self, source_path: str, target_path: str, project_dir: str,
                 is_dir: t.Optional[bool] = None, check_is_dir: bool = False):
        source_path = os.path.normpath(os.path.join(project_dir, source_path))
        target_path = os.path.normpath(target_path)
        if target_path.startswith('/') or target_path.startswith('../'):
            raise ValueError('target_path cannot be absolute or go upwards.')
        if is_dir is not None:
            if check_is_dir:
                raise ValueError('check_is_dir cannot be True if is_dir is not None.')
            self.is_dir = is_dir
        else:
            if check_is_dir:
                self.is_dir = os.path.isdir(source_path)
            else:
                self.is_dir = source_path.endswith('/')
        self.display_source_path = \
            relative_path_if_below(source_path) \
            + ('/' if self.is_dir else '')
        self.display_target_path = \
            relative_path(target_path) \
            + ('/' if self.is_dir else '')
        self.relative_source_path = \
            relative_path_if_below(source_path, project_dir) \
            + ('/' if self.is_dir else '')
        self.relative_target_path = \
            relative_path(target_path) \
            + ('/' if self.is_dir else '')
        self.absolute_source_path = os.path.abspath(source_path) + ('/' if self.is_dir else '')
        self.rsync_source_path = self.absolute_source_path
        self.rsync_target_path = target_path


def load_last_backup_directory(project_dir: str) -> t.Optional[str]:
    path = os.path.join(project_dir, LAST_BACKUP_DIR_FILENAME)
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as f:
            value = f.readline().strip()
            if value != '' and not '..' in value and not value.startswith('/'):
                return value


def save_last_backup_directory(project_dir: str, value: str) -> None:
    path = os.path.join(project_dir, LAST_BACKUP_DIR_FILENAME)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(value + '\n')


def do_backup_content(
    rsync_config: RsyncConfig,
    new_backup_dir: str, old_backup_dir: t.Optional[str], content: str,
    target_file_name: str, dry_run: bool,
    rich_node: rich.tree.Tree
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        source = os.path.join(tmp_dir, target_file_name)
        with open(source, 'w', encoding='utf-8') as f:
            f.write(content)
        cmd = run_rsync_backup_with_hardlinks(
            config=rsync_config,
            source=source,
            new_backup=os.path.join(new_backup_dir, target_file_name),
            old_backup_dirs=[old_backup_dir] if old_backup_dir is not None else [],
            dry_run=dry_run
        )
        rich_node.add(str(format_cmd_line(cmd)))


def do_backup_job(
    rsync_config: RsyncConfig,
    new_backup_dir: str, old_backup_dir: t.Optional[str],
    job: BackupJob, dry_run: bool,
    rich_node: rich.tree.Tree
):
    if old_backup_dir is not None:
        old_backup_path = os.path.normpath(os.path.join(old_backup_dir, job.rsync_target_path))
        if not job.is_dir:
            old_backup_path = os.path.dirname(old_backup_path)
    else:
        old_backup_path = None
    cmd = run_rsync_backup_with_hardlinks(
        config=rsync_config,
        source=job.rsync_source_path,
        new_backup=os.path.join(new_backup_dir, job.rsync_target_path),
        old_backup_dirs=[old_backup_path] if old_backup_path is not None else [],
        dry_run=dry_run
    )
    rich_node.add(str(format_cmd_line(cmd)))


def create_target_structure(
    rsync_config: RsyncConfig,
    new_backup_dir: str, jobs: t.Iterable[BackupJob], dry_run: bool,
    rich_node: rich.tree.Tree
):
    """Create target directory structure at destination

    Required as long as remote rsync does not implement --mkpath
    """

    paths = set(
        os.path.dirname(os.path.normpath(os.path.join(new_backup_dir, job.rsync_target_path)))
        for job in jobs
    )
    leafs = [leaf for leaf in paths if
             leaf != '' and next((path for path in paths if path.startswith(f"{leaf}/")), None) is None]

    with tempfile.TemporaryDirectory() as tmp_dir:
        for leaf in leafs:
            os.makedirs(os.path.join(tmp_dir, leaf))
        cmd = run_rsync_without_delete(
            config=rsync_config,
            source=f"{tmp_dir}/",
            destination='',
            dry_run=dry_run
        )
        rich_node.add(str(format_cmd_line(cmd)))
