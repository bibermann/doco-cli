import dataclasses
import json
import os
import pathlib
import subprocess
import tempfile
import typing as t

import rich.json
import rich.panel
import rich.tree
import typer

from src.utils.backup import BACKUP_CONFIG_JSON
from src.utils.bbak import BbakContextObject
from src.utils.common import dir_from_path
from src.utils.common import PrintCmdData
from src.utils.completers_autocompletion import LegacyPathCompleter
from src.utils.doco_config import DocoConfig
from src.utils.exceptions_rich import DocoError
from src.utils.restore import get_backup_directory
from src.utils.restore import RestoreJob
from src.utils.restore_rich import create_target_structure
from src.utils.restore_rich import do_restore_job
from src.utils.restore_rich import print_details
from src.utils.rich import Formatted
from src.utils.rich import rich_print_cmd
from src.utils.rich import RichAbortCmd
from src.utils.rsync import run_rsync_download_incremental
from src.utils.validators import project_name_callback


@dataclasses.dataclass
class RestoreOptions:
    paths: t.Optional[list[pathlib.Path]]
    workdir: str
    backup: str
    show_progress: bool
    rsync_verbose: bool
    dry_run: bool
    dry_run_verbose: bool


def do_restore(
    options: RestoreOptions,
    jobs: list[RestoreJob],
    project_for_filter: str,
    doco_config: DocoConfig,
    cmds: list[PrintCmdData],
):
    create_target_structure(
        structure_config=doco_config.backup.restore_structure,
        jobs=jobs,
        dry_run=options.dry_run,
        cmds=cmds,
    )

    for job in jobs:
        do_restore_job(
            rsync_config=doco_config.backup.rsync,
            job=job,
            project_for_filter=project_for_filter,
            show_progress=options.show_progress,
            verbose=options.rsync_verbose,
            dry_run=options.dry_run,
            cmds=cmds,
        )


def restore_files(  # noqa: C901 CFQ001 (too complex, max allowed length)
    project_name: str, options: RestoreOptions, doco_config: DocoConfig
):
    # pylint: disable=too-many-locals
    backup_dir = get_backup_directory(
        doco_config.backup.rsync,
        project_name=project_name,
        backup_id=options.backup,
        show_progress=options.show_progress,
        verbose=options.rsync_verbose,
        print_cmd_callback=rich_print_cmd,
    )

    backup_config: t.Mapping[str, t.Any] = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, BACKUP_CONFIG_JSON)
        try:
            run_rsync_download_incremental(
                doco_config.backup.rsync,
                source=f"{project_name}/{backup_dir}/{BACKUP_CONFIG_JSON}",
                destination=os.path.join(tmp_dir, BACKUP_CONFIG_JSON),
                project_for_filter=project_name,
                show_progress=options.show_progress,
                verbose=options.rsync_verbose,
                dry_run=False,
                print_cmd_callback=rich_print_cmd,
                extra_args=["--ignore-missing-args"],
            )
        except subprocess.CalledProcessError as e:
            raise RichAbortCmd(e) from e
        if not pathlib.Path(config_path).exists():
            raise DocoError(
                f"'{BACKUP_CONFIG_JSON}' not found on remote machine.\n"
                "Cannot restore backup, please use download command instead."
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

    if options.paths:
        deep = backup_config.get("deep", True)
        if not deep:
            raise DocoError(
                "Cannot restore specific paths "
                "when '[b bright_cyan]--deep[/]' was not set while creating the backup.\n"
                "Please restore the whole backup or use download command instead."
            )
        backup_paths = (
            [
                os.path.abspath(path),
                os.path.join("files", dir_from_path(os.path.abspath(path), deep=True)),
            ]
            for path in options.paths
        )
        check_is_dir = True
    else:
        backup_paths = backup_config.get("tasks", {}).get("backup_paths", [])
        check_is_dir = False

    jobs: list[RestoreJob] = []

    for backup_paths_item in backup_paths:
        jobs.append(
            RestoreJob(
                source_root_path=backup_config["backup_dir"],
                source_path=backup_paths_item[1],
                target_path=backup_paths_item[0],
                project_dir=options.workdir,
                check_is_dir=check_is_dir,
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

    cmds: list[PrintCmdData] = []

    do_restore(options=options, jobs=jobs, project_for_filter=project_name, doco_config=doco_config, cmds=cmds)

    if options.dry_run:
        print_details(tree, backup_dir_node, backup_config, cmds, options.dry_run_verbose)


def main(  # noqa: CFQ002 (max arguments)
    ctx: typer.Context,
    project: str = typer.Argument(
        ..., callback=project_name_callback, help="Source project to retrieve backups from."
    ),
    paths: t.Optional[list[pathlib.Path]] = typer.Argument(
        None,
        autocompletion=LegacyPathCompleter().__call__,
        exists=True,
        help="Paths to restore (not relative to --workdir but to the caller's CWD).",
        show_default="Paths listed in the backup config",
    ),
    backup: str = typer.Option("0", "--backup", "-b", help="Backup index or name."),
    show_progress: bool = typer.Option(False, "--progress", help="Show rsync progress."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Print more details."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually restore a backup, only show what would be done."
    ),
    skip_root_check: bool = typer.Option(
        False, "--skip-root-check", help="Do not cancel when not run with root privileges."
    ),
):
    """
    Restore a backup.
    """

    obj: BbakContextObject = ctx.obj

    if not skip_root_check and not (dry_run or os.geteuid() == 0):
        raise DocoError(
            "You need to have root privileges to create/download/restore a backup.\n"
            "Please try again, this time using 'sudo'."
        )

    if not obj.doco_config.backup.rsync.is_complete():
        raise DocoError(
            "You need to configure rsync to work with backups.\n"
            "You may want to adjust '[b green]-c[/]' / '[b bright_cyan]--config[/]' "
            "or '[b green]-w[/]' / '[b bright_cyan]--workdir[/]'.\n"
            "Please see documentation for 'doco.config.toml'.",
            formatted=True,
        )

    restore_files(
        project_name=project,
        options=RestoreOptions(
            paths=paths,
            workdir=obj.workdir,
            backup=backup,
            show_progress=show_progress,
            rsync_verbose=verbose,
            dry_run=dry_run,
            dry_run_verbose=verbose,
        ),
        doco_config=obj.doco_config,
    )

    return 0
