import dataclasses
import os
import pathlib
import typing as t

import rich
import rich.pretty
import rich.tree
import typer

from utils.bbak import BbakContextObject
from utils.completers import DirectoryCompleter
from utils.doco_config import DocoConfig
from utils.exceptions_rich import DocoError
from utils.restore import get_backup_directory
from utils.rich import format_cmd_line
from utils.rich import rich_print_cmd
from utils.rsync import run_rsync_download_incremental


@dataclasses.dataclass
class DownloadOptions:
    project_name: str
    backup: str
    destination: str
    dry_run: bool


def download_backup(options: DownloadOptions, doco_config: DocoConfig):
    backup_dir = get_backup_directory(doco_config.backup.rsync,
                                      project_name=options.project_name,
                                      backup_id=options.backup,
                                      print_cmd_callback=rich_print_cmd)

    if not options.dry_run and os.path.exists(options.destination):
        answer = input(f"The directory {os.path.abspath(options.destination)} already exists.\n"
                       f"Enter '{options.destination}' to overwrite (files may get deleted): ")
        if answer != options.destination:
            exit('Cancelled.')

    cmd = run_rsync_download_incremental(doco_config.backup.rsync,
                                         source=f"{options.project_name}/{backup_dir}/",
                                         destination=f"{options.destination}/",
                                         dry_run=options.dry_run,
                                         print_cmd_callback=rich_print_cmd)

    if options.dry_run:
        run_node = rich.tree.Tree('[i]Would run[/]')
        run_node.add(str(format_cmd_line(cmd)))
        rich.print(run_node)


def main(
    ctx: typer.Context,
    backup: str = typer.Option('0', '--backup', '-b',
                               help='Backup index or name.'),
    destination: t.Optional[pathlib.Path] = typer.Option(None, '--destination', '-d',
                                                         autocompletion=DirectoryCompleter().__call__,
                                                         file_okay=False,
                                                         help='Destination (not relative to --workdir but to the caller\'s CWD), defaults to --project within --workdir.'),
    dry_run: bool = typer.Option(False, '--dry-run', '-n',
                                 help='Do not actually download, only show what would be done.'),
):
    """
    Download a backup for local analysis.
    """

    obj: BbakContextObject = ctx.obj

    if not (dry_run or os.geteuid() == 0):
        raise DocoError("You need to have root privileges to load a backup.\n"
                        "Please try again, this time using 'sudo'.")

    if obj.project_id is None:
        raise DocoError(
            "You must specify '[b green]-p[/]' / '[b bright_cyan]--project[/]' before the '[b bright_cyan]get[/]' command.",
            formatted=True,
        )

    if obj.doco_config.backup.rsync.host == '' or obj.doco_config.backup.rsync.module == '':
        raise DocoError("You need to configure rsync to get a backup.\n"
                        "You may want to adjust '[b green]-w[/]' / '[b bright_cyan]--workdir[/]'.\n"
                        "Please see documentation for 'doco.config.json'.", formatted=True)

    download_backup(
        DownloadOptions(
            project_name=obj.project_id,
            backup=backup,
            destination=os.path.normpath(
                str(destination) if destination is not None
                else os.path.join(obj.workdir, obj.project_id)
            ),
            dry_run=dry_run,
        ),
        doco_config=obj.doco_config,
    )

    return 0
