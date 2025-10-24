import pathlib
import shutil
import time

import pytest

from tests.cli.utils.helpers import TEST_PROJECT_NAME
from tests.cli.utils.helpers import TEST_VOLUME_CONTAINER_NAME
from tests.cli.utils.helpers import TEST_VOLUME_LOCAL_NAME
from tests.cli.utils.helpers import then_dirs_match
from tests.cli.utils.helpers import when_running_doco


def when_having_initial_source_files_for_backup(
    *, doco_config_path: pathlib.Path, compose_project_files_path: pathlib.Path, local_data_dir: pathlib.Path
):
    shutil.copytree(compose_project_files_path, local_data_dir / "srv")

    shutil.copy(doco_config_path, local_data_dir / "doco.config.toml")


def when_changing_source_files(*, local_data_dir: pathlib.Path):
    (local_data_dir / "srv" / TEST_PROJECT_NAME / ".env").write_text("Foo=changed")
    (local_data_dir / "srv" / TEST_VOLUME_LOCAL_NAME / "test.txt").write_text("Test S1 rw changed")


def then_files_match_backup(
    backup_name: str,
    *,
    remote_data_dir: pathlib.Path,
    local_data_dir: pathlib.Path,
    having_last_backup_file: bool = True,
):
    then_dirs_match(
        local_data_dir / "srv" / TEST_PROJECT_NAME,
        remote_data_dir / TEST_PROJECT_NAME / backup_name / "project-files",
        ignore=[".last-backup-dir"] if having_last_backup_file else [],
    )
    then_dirs_match(
        local_data_dir / "srv" / TEST_VOLUME_LOCAL_NAME,
        remote_data_dir
        / TEST_PROJECT_NAME
        / backup_name
        / "volumes"
        / "doco-test-s1"
        / TEST_VOLUME_CONTAINER_NAME,
    )

    last_backup_file = local_data_dir / "srv" / TEST_PROJECT_NAME / ".last-backup-dir"
    if having_last_backup_file:
        assert last_backup_file.read_text().strip() == f"{TEST_PROJECT_NAME}/{backup_name}"
    else:
        assert not last_backup_file.exists()


@pytest.mark.usefixtures("rsync_daemon")
def test_backup_and_restore(
    doco_config_path, clean_remote_data_dir, clean_local_data_dir, doco_test_compose_project_files_path
):
    base_raw_backups_doco_args = [
        "backups",
    ]

    def backup_doco_args(backup_name: str) -> list[str]:
        return [
            *base_raw_backups_doco_args,
            "create",
            "--skip-root-check",
            "--deep",
            "--backup",
            backup_name,
            str(clean_local_data_dir / "srv" / TEST_PROJECT_NAME),
        ]

    def restore_backup_doco_args(backup_name: str) -> list[str]:
        return [
            *base_raw_backups_doco_args,
            "restore",
            "--skip-root-check",
            "--backup",
            backup_name,
            str(clean_local_data_dir / "srv" / TEST_PROJECT_NAME),
        ]

    when_having_initial_source_files_for_backup(
        doco_config_path=doco_config_path,
        compose_project_files_path=doco_test_compose_project_files_path,
        local_data_dir=clean_local_data_dir,
    )

    when_running_doco(doco_args=backup_doco_args("backup1"))

    then_files_match_backup(
        "backup1", remote_data_dir=clean_remote_data_dir, local_data_dir=clean_local_data_dir
    )

    when_changing_source_files(local_data_dir=clean_local_data_dir)

    time.sleep(1)  # wait 1 sec to ensure backup2 has a different timestamp.
    when_running_doco(doco_args=backup_doco_args("backup2"))

    then_files_match_backup(
        "backup2", remote_data_dir=clean_remote_data_dir, local_data_dir=clean_local_data_dir
    )

    when_running_doco(doco_args=restore_backup_doco_args("backup1"))

    then_files_match_backup(
        "backup1",
        remote_data_dir=clean_remote_data_dir,
        local_data_dir=clean_local_data_dir,
        having_last_backup_file=False,
    )
