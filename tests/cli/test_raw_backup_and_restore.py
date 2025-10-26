import pathlib
import shutil
import time

import pytest

from tests.cli.utils.helpers import TEST_PROJECT_NAME
from tests.cli.utils.helpers import then_dirs_match
from tests.cli.utils.helpers import when_running_doco
from tests.cli.utils.raw_backup_helpers import raw_remote_content_root
from tests.cli.utils.raw_backup_helpers import when_changing_raw_source_files
from tests.cli.utils.raw_backup_helpers import when_having_initial_source_files_for_raw_backup


def then_files_match_raw_backup(
    backup_name: str,
    *,
    remote_data_dir: pathlib.Path,
    local_data_dir: pathlib.Path,
    local_instance_workdir: pathlib.Path,
    check_last_backup_file: bool = True,
    deep: bool,
):
    then_dirs_match(
        local_data_dir,
        raw_remote_content_root(
            backup_name, remote_data_dir=remote_data_dir, local_data_dir=local_data_dir, deep=deep
        ),
    )

    last_backup_file = local_instance_workdir / f"{TEST_PROJECT_NAME}.last-backup-dir"
    if check_last_backup_file:
        assert last_backup_file.read_text().strip() == f"{TEST_PROJECT_NAME}/{backup_name}"


@pytest.mark.parametrize("deep", [True, False])
@pytest.mark.usefixtures("rsync_daemon")
def test_raw_backup_and_restore(  # noqa: CFQ001 (max allowed length)
    doco_config_path, clean_remote_data_dir, clean_local_data_dir, clean_local_instance_workdir, deep: bool
):
    base_raw_backups_doco_args = [
        "backups",
        "raw",
        "--workdir",
        clean_local_instance_workdir,
    ]

    def backup_doco_args(backup_name: str) -> list[str]:
        return [
            *base_raw_backups_doco_args,
            "create",
            "--skip-root-check",
            *(["--deep"] if deep else []),
            "--backup",
            backup_name,
            TEST_PROJECT_NAME,
            str(clean_local_data_dir),
        ]

    list_projects_doco_args = [
        *base_raw_backups_doco_args,
        "ls",
    ]

    list_backups_doco_args = [
        *base_raw_backups_doco_args,
        "ls",
        TEST_PROJECT_NAME,
    ]

    def download_backup_doco_args(backup_name: str) -> list[str]:
        return [
            *base_raw_backups_doco_args,
            "download",
            "--skip-root-check",
            "--backup",
            backup_name,
            TEST_PROJECT_NAME,
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

    when_running_doco(doco_args=backup_doco_args("backup1"))

    then_files_match_raw_backup(
        "backup1",
        remote_data_dir=clean_remote_data_dir,
        local_data_dir=clean_local_data_dir,
        local_instance_workdir=clean_local_instance_workdir,
        deep=deep,
    )

    when_changing_raw_source_files(local_data_dir=clean_local_data_dir)

    time.sleep(1)  # wait 1 sec to ensure backup2 has a different timestamp.
    when_running_doco(doco_args=backup_doco_args("backup2"))

    then_files_match_raw_backup(
        "backup2",
        remote_data_dir=clean_remote_data_dir,
        local_data_dir=clean_local_data_dir,
        local_instance_workdir=clean_local_instance_workdir,
        deep=deep,
    )

    output = when_running_doco(doco_args=list_projects_doco_args)

    assert output.strip().endswith(f"/\n└── {TEST_PROJECT_NAME}")

    output = when_running_doco(doco_args=list_backups_doco_args)

    assert output.strip().endswith(f"{TEST_PROJECT_NAME}\n├── 0: backup2\n└── 1: backup1")

    for backup_name in ["backup1", "backup2"]:
        shutil.rmtree(clean_local_instance_workdir / TEST_PROJECT_NAME, ignore_errors=True)

        when_running_doco(doco_args=download_backup_doco_args(backup_name))

        then_dirs_match(
            clean_remote_data_dir / TEST_PROJECT_NAME / backup_name,
            clean_local_instance_workdir / TEST_PROJECT_NAME,
        )

    for backup_name in ["backup1", "backup2"]:
        when_running_doco(doco_args=restore_backup_doco_args(backup_name))

        then_files_match_raw_backup(
            backup_name,
            remote_data_dir=clean_remote_data_dir,
            local_data_dir=clean_local_data_dir,
            local_instance_workdir=clean_local_instance_workdir,
            check_last_backup_file=False,
            deep=deep,
        )
