import dataclasses
import os
import typing as t

from src.utils.common import print_cmd
from src.utils.common import PrintCmdCallable
from src.utils.common import relative_path
from src.utils.common import relative_path_if_below
from src.utils.rsync import RsyncConfig
from src.utils.rsync import run_rsync_list


@dataclasses.dataclass
class RestoreJob:
    # pylint: disable=too-many-instance-attributes
    display_source_path: str
    display_target_path: str
    relative_source_path: str
    relative_target_path: str
    rsync_source_path: str
    rsync_target_path: str
    is_dir: bool

    def __init__(self, source_path: str, target_path: str, project_dir: str, is_dir: t.Optional[bool] = None):
        target_path_seems_dir = target_path.endswith("/")
        target_path = os.path.normpath(os.path.join(project_dir, target_path))
        source_path = os.path.normpath(source_path)
        if source_path.startswith("/") or source_path.startswith("../"):
            raise ValueError("source_path cannot be absolute or go upwards.")
        if is_dir is not None:
            self.is_dir = is_dir
        else:
            self.is_dir = target_path_seems_dir
        self.display_target_path = relative_path_if_below(target_path) + ("/" if self.is_dir else "")
        self.display_source_path = relative_path(source_path) + ("/" if self.is_dir else "")
        self.relative_target_path = relative_path_if_below(target_path, project_dir) + (
            "/" if self.is_dir else ""
        )
        self.relative_source_path = relative_path(source_path) + ("/" if self.is_dir else "")
        self.absolute_target_path = os.path.abspath(target_path) + ("/" if self.is_dir else "")
        self.rsync_target_path = self.absolute_target_path
        self.rsync_source_path = source_path


def get_backup_directory(
    rsync_config: RsyncConfig,
    project_name: str,
    backup_id: str,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> str:
    if backup_id.isnumeric():
        _, file_list = run_rsync_list(
            rsync_config, target=f"{project_name}/", dry_run=False, print_cmd_callback=print_cmd_callback
        )
        return sorted([file for file in file_list if file.startswith("backup-")], reverse=True)[int(backup_id)]
    return f"backup-{backup_id}"
