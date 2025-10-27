import pathlib

import pytest

import src.utils.common
from tests.cli.utils.helpers import TEST_PROJECT_NAME
from tests.cli.utils.helpers import then_dirs_match
from tests.cli.utils.helpers import when_running_doco
from tests.cli.utils.raw_backup_helpers import raw_remote_content_root
from tests.cli.utils.raw_backup_helpers import SUBPATH_TO_RESTORE
from tests.cli.utils.raw_backup_helpers import when_having_initial_source_files_for_raw_backup


def when_changing_source_files(*, local_data_dir: pathlib.Path):
    (local_data_dir / "initial_file.txt").write_text("Initial content modified")
    (local_data_dir / SUBPATH_TO_RESTORE / "some-file").write_text("some file modified")


def than_only_some_dir_was_restored(*, local_data_dir: pathlib.Path):
    assert (local_data_dir / "initial_file.txt").read_text().strip() == "Initial content modified"
    assert (local_data_dir / SUBPATH_TO_RESTORE / "some-file").read_text().strip() == "some file"


def then_files_match_raw_incremental_backup(
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
        assert last_backup_file.read_text().strip() == f"{TEST_PROJECT_NAME}/before"


@pytest.mark.parametrize("deep", [True, False])
@pytest.mark.parametrize("incremental", [True, False])
@pytest.mark.usefixtures("rsync_daemon")
def test_raw_restore_path(  # noqa: CFQ001 (max allowed length)
    doco_config_path,
    clean_remote_data_dir,
    clean_local_data_dir,
    clean_local_instance_workdir,
    deep: bool,
    incremental: bool,
):
    remote_subpath_path = (
        pathlib.Path("files")
        / src.utils.common.dir_from_path(str(clean_local_data_dir), deep=deep)
        / SUBPATH_TO_RESTORE
    )

    base_raw_backups_doco_args = [
        "backups",
        "raw",
        "--workdir",
        clean_local_instance_workdir,
    ]
    doco_args = [
        *base_raw_backups_doco_args,
        "create",
        *(["--deep"] if deep else []),
        *(["--incremental"] if incremental else []),
        "--skip-root-check",
        "--backup",
        "backup",
        TEST_PROJECT_NAME,
        str(clean_local_data_dir),
    ]
    download_backup_subpath_doco_args = [
        *base_raw_backups_doco_args,
        "download",
        "--skip-root-check",
        TEST_PROJECT_NAME,
        str(remote_subpath_path),
    ]
    restore_backup_subpath_doco_args = [
        *base_raw_backups_doco_args,
        "restore",
        "--skip-root-check",
        TEST_PROJECT_NAME,
        str(clean_local_data_dir / SUBPATH_TO_RESTORE),
    ]

    when_having_initial_source_files_for_raw_backup(
        doco_config_path=doco_config_path,
        local_data_dir=clean_local_data_dir,
        local_instance_workdir=clean_local_instance_workdir,
    )

    when_running_doco(doco_args=doco_args)

    when_changing_source_files(local_data_dir=clean_local_data_dir)

    if deep:
        when_running_doco(doco_args=restore_backup_subpath_doco_args)

        than_only_some_dir_was_restored(local_data_dir=clean_local_data_dir)
    else:
        with pytest.raises(AssertionError):
            when_running_doco(doco_args=restore_backup_subpath_doco_args)

    # shutil.rmtree(clean_local_instance_workdir / TEST_PROJECT_NAME, ignore_errors=True)

    when_running_doco(doco_args=download_backup_subpath_doco_args)

    then_dirs_match(
        clean_remote_data_dir / TEST_PROJECT_NAME / "backup" / remote_subpath_path,
        clean_local_instance_workdir / TEST_PROJECT_NAME / SUBPATH_TO_RESTORE,
    )
