import pathlib
import shutil

import src.utils.common
from tests.cli.utils.helpers import TEST_PROJECT_NAME


def raw_remote_content_root(
    backup_name: str,
    *,
    remote_data_dir: pathlib.Path,
    local_data_dir: pathlib.Path,
    deep: bool,
) -> pathlib.Path:
    return (
        remote_data_dir
        / TEST_PROJECT_NAME
        / backup_name
        / "files"
        / str(src.utils.common.dir_from_path(str(local_data_dir), deep=deep))
    )


def when_having_initial_source_files_for_raw_backup(
    *, doco_config_path: pathlib.Path, local_data_dir: pathlib.Path, local_instance_workdir: pathlib.Path
):
    (local_data_dir / "initial_file.txt").write_text("Initial content")

    shutil.copy(doco_config_path, local_instance_workdir / "doco.config.toml")


def when_changing_raw_source_files(*, local_data_dir: pathlib.Path):
    (local_data_dir / "additional_file.txt").write_text("Additional content")
    (local_data_dir / "initial_file.txt").write_text("Modified content")
