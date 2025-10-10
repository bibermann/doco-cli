import sys
import typing as t

import typer

from src.utils.completers_autocompletion import LegacyComposeProjectCompleter


def projects_callback(ctx: typer.Context, projects: t.Union[list[str], None]) -> t.Union[list[str], None]:
    if ctx.resilient_parsing:
        return projects
    if not projects or len(projects) == 0:
        return ["."] if sys.stdin.isatty() else sys.stdin.read().strip().splitlines()
    return projects


PROJECTS_ARGUMENT = typer.Argument(
    None,
    callback=projects_callback,
    autocompletion=LegacyComposeProjectCompleter().__call__,
    help="Compose files and/or directories containing a \\[docker-]compose.y\\[a]ml.",
    show_default="stdin or current directory",
)
RUNNING_OPTION = typer.Option(
    False, "--running", help="Consider only projects with at least one running or restarting service."
)
