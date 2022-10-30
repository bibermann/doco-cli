import dataclasses
import os
import typing as t

from src.utils.common import relative_path
from src.utils.common import relative_path_if_below

BACKUP_CONFIG_JSON = "config.json"
LAST_BACKUP_DIR_FILENAME = ".last-backup-dir"


@dataclasses.dataclass
class BackupJob:
    # pylint: disable=too-many-instance-attributes
    display_source_path: str
    display_target_path: str
    relative_source_path: str
    relative_target_path: str
    rsync_source_path: str
    rsync_target_path: str
    is_dir: bool

    def __init__(
        self,
        source_path: str,
        target_path: str,
        project_dir: str,
        is_dir: t.Optional[bool] = None,
        check_is_dir: bool = False,
    ):
        source_path_seems_dir = source_path.endswith("/")
        source_path = os.path.normpath(os.path.join(project_dir, source_path))
        target_path = os.path.normpath(target_path)
        if target_path.startswith("/") or target_path.startswith("../"):
            raise ValueError("target_path cannot be absolute or go upwards.")
        if is_dir is not None:
            if check_is_dir:
                raise ValueError("check_is_dir cannot be True if is_dir is not None.")
            self.is_dir = is_dir
        else:
            if check_is_dir:
                self.is_dir = os.path.isdir(source_path)
            else:
                self.is_dir = source_path_seems_dir
        self.display_source_path = relative_path_if_below(source_path) + ("/" if self.is_dir else "")
        self.display_target_path = relative_path(target_path) + ("/" if self.is_dir else "")
        self.relative_source_path = relative_path_if_below(source_path, project_dir) + (
            "/" if self.is_dir else ""
        )
        self.relative_target_path = relative_path(target_path) + ("/" if self.is_dir else "")
        self.absolute_source_path = os.path.abspath(source_path) + ("/" if self.is_dir else "")
        self.rsync_source_path = self.absolute_source_path
        self.rsync_target_path = target_path + ("/" if self.is_dir else "")


def load_last_backup_directory(project_dir: str, file_name: str = LAST_BACKUP_DIR_FILENAME) -> t.Optional[str]:
    path = os.path.join(project_dir, file_name)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            value = f.readline().strip()
            if value != "" and ".." not in value and not value.startswith("/"):
                return value
    return None


def save_last_backup_directory(
    project_dir: str, value: str, file_name: str = LAST_BACKUP_DIR_FILENAME
) -> None:
    path = os.path.join(project_dir, file_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(value + "\n")
