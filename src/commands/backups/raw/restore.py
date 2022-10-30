import dataclasses
import json
import os
import tempfile
import typing as t

import rich.json
import rich.panel
import rich.tree
import typer

from src.utils.backup import BACKUP_CONFIG_JSON
from src.utils.bbak import BbakContextObject
from src.utils.doco_config import DocoConfig
from src.utils.exceptions_rich import DocoError
from src.utils.restore import get_backup_directory
from src.utils.restore import RestoreJob
from src.utils.restore_rich import create_target_structure
from src.utils.restore_rich import do_restore_job
from src.utils.rich import Formatted
from src.utils.rich import rich_print_cmd
from src.utils.rsync import run_rsync_download_incremental
from src.utils.validators import project_name_callback


@dataclasses.dataclass
class RestoreOptions:
    workdir: str
    backup: str
    dry_run: bool
    dry_run_verbose: bool


def do_restore(
    options: RestoreOptions, jobs: list[RestoreJob], doco_config: DocoConfig, run_node: rich.tree.Tree
):
    create_target_structure(jobs=jobs, dry_run=options.dry_run, rich_node=run_node)

    for job in jobs:
        do_restore_job(
            rsync_config=doco_config.backup.rsync, job=job, dry_run=options.dry_run, rich_node=run_node
        )


def restore_files(project_name: str, options: RestoreOptions, doco_config: DocoConfig):
    # pylint: disable=too-many-locals
    backup_dir = get_backup_directory(
        doco_config.backup.rsync,
        project_name=project_name,
        backup_id=options.backup,
        print_cmd_callback=rich_print_cmd,
    )

    backup_config: t.Any = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, BACKUP_CONFIG_JSON)
        run_rsync_download_incremental(
            doco_config.backup.rsync,
            source=f"{project_name}/{backup_dir}/{BACKUP_CONFIG_JSON}",
            destination=os.path.join(tmp_dir, BACKUP_CONFIG_JSON),
            dry_run=False,
            print_cmd_callback=rich_print_cmd,
        )
        with open(config_path, encoding="utf-8") as f:
            backup_config = json.load(f)

    project_id = f"[b]{Formatted(project_name)}[/]"

    tree = rich.tree.Tree(str(project_id))
    backup_dir_node = tree.add(f"[i]Backup directory:[/] [b]{Formatted(backup_dir)}[/]")

    if backup_config.get("backup_tool", "") != "bbak":
        config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
        backup_dir_node.add(config_group)

        config_group.renderables.append(
            rich.panel.Panel(
                rich.json.JSON(json.dumps(backup_config, indent=4)), expand=False, border_style="green"
            )
        )

        raise DocoError("The config does not look like a bbak config.")

    backup_node = tree.add("[i]Backup items[/]")

    backup_paths = backup_config.get("tasks", {}).get("backup_paths", [])

    jobs: list[RestoreJob] = []

    for backup_paths_item in backup_paths:
        jobs.append(
            RestoreJob(
                source_path=backup_paths_item[1], target_path=backup_paths_item[0], project_dir=options.workdir
            )
        )

    for job in jobs:
        if os.path.exists(job.absolute_target_path):
            action = "[red](override)[/]"
        else:
            action = "(create)"
        backup_node.add(
            f"{job.display_source_path} [dim]->[/] [dark_orange]{job.display_target_path}[/] {action}"
        )

    run_node = rich.tree.Tree("[i]Would run[/]")
    if options.dry_run_verbose:
        tree.add(run_node)

    do_restore(options=options, jobs=jobs, doco_config=doco_config, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
            backup_dir_node.add(config_group)

            config_group.renderables.append(
                rich.panel.Panel(
                    rich.json.JSON(json.dumps(backup_config, indent=4)), expand=False, border_style="green"
                )
            )

        rich.print(tree)


def main(
    ctx: typer.Context,
    project: str = typer.Argument(
        ..., callback=project_name_callback, help="Source project to retrieve backups from."
    ),
    backup: str = typer.Option("0", "--backup", "-b", help="Backup index or name."),
    verbose: bool = typer.Option(False, "--verbose", help="Print more details if --dry-run."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually restore a backup, only show what would be done."
    ),
):
    """
    Restore a backup.
    """

    obj: BbakContextObject = ctx.obj

    if not (dry_run or os.geteuid() == 0):
        raise DocoError(
            "You need to have root privileges to restore a backup.\n"
            "Please try again, this time using 'sudo'."
        )

    if obj.doco_config.backup.rsync.host == "" or obj.doco_config.backup.rsync.module == "":
        raise DocoError(
            "You need to configure rsync to get a backup.\n"
            "You may want to adjust '[b green]-w[/]' / '[b bright_cyan]--workdir[/]'.\n"
            "Please see documentation for 'doco.config.json'.",
            formatted=True,
        )

    restore_files(
        project_name=project,
        options=RestoreOptions(
            workdir=obj.workdir,
            backup=backup,
            dry_run=dry_run,
            dry_run_verbose=verbose,
        ),
        doco_config=obj.doco_config,
    )

    return 0
