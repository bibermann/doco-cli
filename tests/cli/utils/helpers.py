import filecmp
import pathlib
import shutil
import typing
from pathlib import Path

from typer.testing import CliRunner

import src.main


TEST_PROJECT_NAME = "test-project"
TEST_VOLUME_LOCAL_NAME = "s1-volume-rw"
TEST_VOLUME_CONTAINER_NAME = "volume-rw"

runner = CliRunner()


def rmtree_keeping_root(root: Path):
    for item in root.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def then_dirs_match(a: pathlib.Path, b: pathlib.Path, ignore: typing.Union[list[str], None] = None):
    dcmp = filecmp.dircmp(a, b, ignore=ignore or [])

    assert not dcmp.left_only, f"Files only in {a}: {dcmp.left_only}"
    assert not dcmp.right_only, f"Files only in {b}: {dcmp.right_only}"

    assert not dcmp.diff_files, f"Files with different content: {dcmp.diff_files}"

    assert all(filecmp.cmp(a / file, b / file, shallow=False) for file in dcmp.common_files)


def when_running_doco(*, doco_args: list[str]) -> str:
    result = runner.invoke(src.main.app, doco_args)
    print(result.output)
    if result.exception:
        print(result.exception, result.exc_info)
    assert result.exit_code == 0
    return result.output
