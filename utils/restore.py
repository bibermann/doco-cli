import dataclasses
import os
import typing as t

import rich.tree

from utils.common import relative_path
from utils.common import relative_path_if_below
from utils.rich import format_cmd_line
from utils.rsync import RsyncConfig
from utils.rsync import run_rsync_download_incremental
from utils.rsync import run_rsync_list


@dataclasses.dataclass
class RestoreJob:
    display_source_path: str
    display_target_path: str
    relative_source_path: str
    relative_target_path: str
    rsync_source_path: str
    rsync_target_path: str
    is_dir: bool

    def __init__(self, source_path: str, target_path: str, project_dir: str,
                 is_dir: t.Optional[bool] = None):
        target_path = os.path.normpath(os.path.join(project_dir, target_path))
        source_path = os.path.normpath(source_path)
        if source_path.startswith('/') or source_path.startswith('../'):
            raise ValueError('source_path cannot be absolute or go upwards.')
        if is_dir is not None:
            self.is_dir = is_dir
        else:
            self.is_dir = target_path.endswith('/')
        self.display_target_path = \
            relative_path_if_below(target_path) \
            + ('/' if self.is_dir else '')
        self.display_source_path = \
            relative_path(source_path) \
            + ('/' if self.is_dir else '')
        self.relative_target_path = \
            relative_path_if_below(target_path, project_dir) \
            + ('/' if self.is_dir else '')
        self.relative_source_path = \
            relative_path(source_path) \
            + ('/' if self.is_dir else '')
        self.absolute_target_path = os.path.abspath(target_path) + ('/' if self.is_dir else '')
        self.rsync_target_path = self.absolute_target_path
        self.rsync_source_path = source_path


def do_restore_job(
    rsync_config: RsyncConfig,
    job: RestoreJob, dry_run: bool,
    rich_node: rich.tree.Tree
):
    cmd = run_rsync_download_incremental(
        config=rsync_config,
        source=job.rsync_source_path,
        destination=job.rsync_target_path,
        dry_run=dry_run
    )
    rich_node.add(str(format_cmd_line(cmd)))


def create_target_structure(
    jobs: t.Iterable[RestoreJob], dry_run: bool,
    rich_node: rich.tree.Tree
):
    """Create target directory structure at local machine

    Required as long as (remote?) rsync does not implement --mkpath
    """

    paths = set(
        os.path.dirname(os.path.normpath(job.absolute_target_path))
        for job in jobs
    )
    leafs = [leaf for leaf in paths if
             leaf != '' and next((path for path in paths if path.startswith(f"{leaf}/")), None) is None]

    for leaf in leafs:
        if not os.path.isdir(leaf):
            if os.path.exists(leaf):
                raise RuntimeError(f"Error: {leaf} was assumed to be a directory.")
            if not dry_run:
                os.makedirs(leaf)
            else:
                rich_node.add(f"[dim]Create directory[/] {leaf}")


def get_backup_directory(rsync_config: RsyncConfig, project_name: str, backup_id: str) -> str:
    if backup_id.isnumeric():
        _, file_list = run_rsync_list(rsync_config, target=f"{project_name}/",
                                      dry_run=False)
        return sorted(
            [file for file in file_list if file.startswith('backup-')], reverse=True
        )[int(backup_id)]
    else:
        return f"backup-{backup_id}"
