import pathlib

import pytest

from tests.cli.utils.helpers import TEST_PROJECT_NAME
from tests.cli.utils.helpers import then_dirs_match
from tests.cli.utils.helpers import when_running_doco
from tests.cli.utils.raw_backup_helpers import raw_remote_content_root
from tests.cli.utils.raw_backup_helpers import when_having_initial_source_files_for_raw_backup


def then_files_match_raw_incremental_backup(
    backup_name: str,
    *,
    remote_data_dir: pathlib.Path,
    local_data_dir: pathlib.Path,
    local_instance_workdir: pathlib.Path,
    check_last_backup_file: bool = True,
):
    then_dirs_match(
        local_data_dir,
        raw_remote_content_root(backup_name, remote_data_dir=remote_data_dir, local_data_dir=local_data_dir),
    )

    last_backup_file = local_instance_workdir / f"{TEST_PROJECT_NAME}.last-backup-dir"
    if check_last_backup_file:
        assert last_backup_file.read_text().strip() == f"{TEST_PROJECT_NAME}/before"


def when_adding_path1_with_cache(local_data_dir: pathlib.Path):
    (local_data_dir / "path1" / "cache").mkdir(parents=True)
    (local_data_dir / "path1" / "file1").write_text("file1")
    (local_data_dir / "path1" / "cache" / "cache-file").write_text("cache-file")


def when_changing_path1_file1(local_data_dir: pathlib.Path):
    (local_data_dir / "path1" / "file1").write_text("file1 changed")


@pytest.mark.usefixtures("rsync_daemon")
def test_path_based_filter(  # noqa: CFQ001 (max allowed length)
    doco_config_path, clean_remote_data_dir, clean_local_data_dir, clean_local_instance_workdir
):
    remote_backup_root = raw_remote_content_root(
        "backup", remote_data_dir=clean_remote_data_dir, local_data_dir=clean_local_data_dir
    )

    base_raw_backups_doco_args = [
        "backups",
        "raw",
        "--workdir",
        clean_local_instance_workdir,
    ]
    create_backup_doco_args = [
        *base_raw_backups_doco_args,
        "create",
        "--deep",
        "--incremental",
        "--skip-root-check",
        TEST_PROJECT_NAME,
        str(clean_local_data_dir),
        "--incremental-backup",
        "before",
    ]

    def restore_backup_doco_args(backup_name: str) -> list[str]:
        return [
            *base_raw_backups_doco_args,
            "restore",
            "--skip-root-check",
            "--backup",
            backup_name,
            TEST_PROJECT_NAME,
        ]

    when_having_initial_source_files_for_raw_backup(
        doco_config_path=doco_config_path,
        local_data_dir=clean_local_data_dir,
        local_instance_workdir=clean_local_instance_workdir,
    )

    when_adding_path1_with_cache(local_data_dir=clean_local_data_dir)

    when_running_doco(doco_args=create_backup_doco_args)

    assert (remote_backup_root / "path1" / "file1").read_text() == (
        clean_local_data_dir / "path1" / "file1"
    ).read_text()
    assert not (remote_backup_root / "path1" / "cache").exists()

    when_changing_path1_file1(local_data_dir=clean_local_data_dir)

    when_running_doco(doco_args=restore_backup_doco_args("backup"))

    assert (remote_backup_root / "path1" / "file1").read_text() == (
        clean_local_data_dir / "path1" / "file1"
    ).read_text()
    assert (clean_local_data_dir / "path1" / "cache" / "cache-file").exists()
