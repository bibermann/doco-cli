import dataclasses
import os
import pathlib
import subprocess
import typing as t

import typer

from src.utils.bbak import BbakContextObject
from src.utils.common import PrintCmdData
from src.utils.completers import DirectoryCompleter
from src.utils.doco_config import DocoConfig
from src.utils.exceptions_rich import DocoError
from src.utils.restore import get_backup_directory
from src.utils.rich import rich_print_cmd
from src.utils.rich import rich_print_conditional_cmds
from src.utils.rich import RichAbortCmd
from src.utils.rsync import run_rsync_download_incremental
from src.utils.validators import project_name_callback


@dataclasses.dataclass
class DownloadOptions:  # pylint: disable=too-many-instance-attributes
    project_name: str
    backup_path: t.Optional[str]
    backup: str
    destination: str
    with_delete: bool
    show_progress: bool
    rsync_verbose: bool
    dry_run: bool


def download_backup(options: DownloadOptions, doco_config: DocoConfig):
    backup_dir = get_backup_directory(
        doco_config.backup.rsync,
        project_name=options.project_name,
        backup_id=options.backup,
        show_progress=options.show_progress,
        verbose=options.rsync_verbose,
        print_cmd_callback=rich_print_cmd,
    )

    if not options.dry_run and not options.with_delete and os.path.exists(options.destination):
        answer = input(
            f"The directory {os.path.abspath(options.destination)} already exists.\n"
            f"Enter '{options.destination}' to overwrite (files may get overwritten): "
        )
        if answer != options.destination:
            raise typer.Abort()

    try:
        cmd = run_rsync_download_incremental(
            doco_config.backup.rsync,
            source=f"{options.project_name}/{backup_dir}/" + (options.backup_path or ""),
            destination=f"{options.destination}/",
            project_for_filter=options.project_name,
            show_progress=options.show_progress,
            verbose=options.rsync_verbose,
            delete_from_destination=options.with_delete,
            dry_run=options.dry_run,
            print_cmd_callback=rich_print_cmd,
        )
    except subprocess.CalledProcessError as e:
        raise RichAbortCmd(e) from e

    if options.dry_run:
        rich_print_conditional_cmds([PrintCmdData(cmd=cmd)])


def main(  # noqa: CFQ002 (max arguments)
    ctx: typer.Context,
    project: str = typer.Argument(
        ..., callback=project_name_callback, help="Source project to retrieve backups from."
    ),
    backup_path: t.Optional[str] = typer.Argument(
        None, help="Path to restore (relative to to the backup dir).", show_default="."
    ),
    backup: str = typer.Option("0", "--backup", "-b", help="Backup index or name."),
    destination: t.Optional[pathlib.Path] = typer.Option(
        None,
        "--destination",
        "-d",
        shell_complete=DirectoryCompleter().__call__,
        file_okay=False,
        help="Destination (not relative to --workdir but to the caller's CWD), "
        "defaults to --project within --workdir.",
    ),
    with_delete: bool = typer.Option(
        False, "--delete", help="Delete destination files not existing in the backup without confirmation."
    ),
    show_progress: bool = typer.Option(False, "--progress", help="Show rsync progress."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Print more details."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually download, only show what would be done."
    ),
    skip_root_check: bool = typer.Option(
        False, "--skip-root-check", help="Do not cancel when not run with root privileges."
    ),
):
    """
    Download a backup for local analysis.
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

    download_backup(
        DownloadOptions(
            project_name=project,
            backup_path=backup_path,
            backup=backup,
            destination=os.path.normpath(
                str(destination) if destination is not None else os.path.join(obj.workdir, project)
            ),
            with_delete=with_delete,
            show_progress=show_progress,
            rsync_verbose=verbose,
            dry_run=dry_run,
        ),
        doco_config=obj.doco_config,
    )

    return 0
