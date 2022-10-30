import typing as t

import typer

from src.utils.bbak import BbakContextObject
from src.utils.exceptions_rich import DocoError
from src.utils.restore_rich import list_backups
from src.utils.restore_rich import list_projects
from src.utils.validators import project_name_callback


def main(
    ctx: typer.Context,
    project: t.Optional[str] = typer.Argument(
        None,
        callback=project_name_callback,
        help="Project to list backups from. Listing projects if not given.",
    ),
):
    """
    List backups.
    """

    obj: BbakContextObject = ctx.obj

    if obj.doco_config.backup.rsync.host == "" or obj.doco_config.backup.rsync.module == "":
        raise DocoError(
            "You need to configure rsync to get a backup.\n"
            "You may want to adjust '[b green]-w[/]' / '[b bright_cyan]--workdir[/]'.\n"
            "Please see documentation for 'doco.config.json'.",
            formatted=True,
        )

    if project is None:
        list_projects(doco_config=obj.doco_config)
    else:
        list_backups(project_name=project, doco_config=obj.doco_config)
