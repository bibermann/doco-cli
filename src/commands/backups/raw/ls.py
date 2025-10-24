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
    show_progress: bool = typer.Option(False, "--progress", help="Show rsync progress."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Print more details."),
):
    """
    List backups.

    Note that the order of backups is not guaranteed between backups created within the same second.
    """

    obj: BbakContextObject = ctx.obj

    if not obj.doco_config.backup.rsync.is_complete():
        raise DocoError(
            "You need to configure rsync to work with backups.\n"
            "You may want to adjust '[b green]-w[/]' / '[b bright_cyan]--workdir[/]'.\n"
            "Please see documentation for 'doco.config.toml'.",
            formatted=True,
        )

    if project is None:
        list_projects(doco_config=obj.doco_config, show_progress=show_progress, verbose=verbose)
    else:
        list_backups(
            project_name=project, doco_config=obj.doco_config, show_progress=show_progress, verbose=verbose
        )
