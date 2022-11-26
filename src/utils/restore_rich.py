import os
import pathlib
import subprocess
import typing as t

import rich.tree

from src.utils.doco_config import DocoBackupRestoreStructureConfig
from src.utils.doco_config import DocoConfig
from src.utils.restore import RestoreJob
from src.utils.rich import format_cmd_line
from src.utils.rich import Formatted
from src.utils.rich import rich_print_cmd
from src.utils.rich import RichAbortCmd
from src.utils.rsync import RsyncConfig
from src.utils.rsync import run_rsync_download_incremental
from src.utils.rsync import run_rsync_list
from src.utils.system import chown_given_strings


def list_projects(doco_config: DocoConfig):
    try:
        _, date_file_tuples = run_rsync_list(
            doco_config.backup.rsync, target="", dry_run=False, print_cmd_callback=rich_print_cmd
        )
    except subprocess.CalledProcessError as e:
        raise RichAbortCmd(e) from e
    tree = rich.tree.Tree(f"[b]{Formatted(doco_config.backup.rsync.root)}[/]")
    files = sorted([item[1] for item in date_file_tuples])
    for file in files:
        tree.add(f"[yellow]{Formatted(file)}[/]")
    rich.print(tree)


def list_backups(project_name: str, doco_config: DocoConfig):
    try:
        _, date_file_tuples = run_rsync_list(
            doco_config.backup.rsync,
            target=f"{project_name}/",
            dry_run=False,
            print_cmd_callback=rich_print_cmd,
        )
    except subprocess.CalledProcessError as e:
        raise RichAbortCmd(e) from e
    tree = rich.tree.Tree(
        f"[dim]{Formatted(doco_config.backup.rsync.root)}/[/][b]{Formatted(project_name)}[/]"
    )
    files = [item[1] for item in sorted(date_file_tuples, key=lambda item: item[0], reverse=True)]
    for i, file in enumerate(files):
        tree.add(f"[yellow]{i}[/][dim]:[/] {Formatted(file)}")
    rich.print(tree)


def do_restore_job(rsync_config: RsyncConfig, job: RestoreJob, dry_run: bool, rich_node: rich.tree.Tree):
    try:
        cmd = run_rsync_download_incremental(
            config=rsync_config,
            source=job.rsync_source_path,
            destination=job.rsync_target_path,
            dry_run=dry_run,
            print_cmd_callback=rich_print_cmd,
        )
    except subprocess.CalledProcessError as e:
        raise RichAbortCmd(e) from e
    rich_node.add(str(format_cmd_line(cmd)))


def create_target_structure(
    structure_config: DocoBackupRestoreStructureConfig,
    jobs: t.Iterable[RestoreJob],
    dry_run: bool,
    rich_node: rich.tree.Tree,
):
    """Create target directory structure at local machine

    Required as long as (remote?) rsync does not implement --mkpath
    """

    paths = set(os.path.dirname(os.path.normpath(job.absolute_target_path)) for job in jobs)
    leafs = [
        leaf
        for leaf in paths
        if leaf != "" and next((path for path in paths if path.startswith(f"{leaf}/")), None) is None
    ]

    for leaf in leafs:
        if not os.path.isdir(leaf):
            if os.path.exists(leaf):
                raise RuntimeError(f"Error: {leaf} was assumed to be a directory.")
            if not dry_run:
                existing_parent = pathlib.Path(leaf)
                while not existing_parent.exists():
                    existing_parent = existing_parent.parent
                os.makedirs(leaf)
                for root, dirs, _ in os.walk(existing_parent):
                    for name in dirs:
                        chown_given_strings(
                            os.path.join(root, name), structure_config.uid, structure_config.gid
                        )
            else:
                rich_node.add(f"[dim]Create directory[/] {leaf}")
