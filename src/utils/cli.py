import sys

import typer

from src.utils.completers import ComposeProjectCompleter


def projects_callback(ctx: typer.Context, projects: list[str]) -> list[str]:
    if ctx.resilient_parsing:
        return projects
    if len(projects) == 0:
        return ["."] if sys.stdin.isatty() else sys.stdin.read().strip().splitlines()
    return projects


PROJECTS_ARGUMENT = typer.Argument(
    None,
    callback=projects_callback,
    shell_complete=ComposeProjectCompleter().__call__,
    help="Compose files and/or directories containing a docker-compose.y\\[a]ml.",
    show_default="stdin or current directory",
)
RUNNING_OPTION = typer.Option(
    False, "--running", "-r", help="Consider only projects with at least one running or restarting service."
)
