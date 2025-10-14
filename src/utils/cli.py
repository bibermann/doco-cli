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


def comma_separated_list_callback(ctx: typer.Context, args: list[str]) -> list[str]:
    if ctx.resilient_parsing:
        return args
    items: list[str] = []
    for value in args:
        items.extend(stripped_item for item in value.split(",") if (stripped_item := item.strip()))
    return items


PROJECTS_ARGUMENT = typer.Argument(
    None,
    callback=projects_callback,
    autocompletion=LegacyComposeProjectCompleter().__call__,
    help="Compose files and/or directories containing a \\[docker-]compose.y\\[a]ml.",
    show_default="stdin or current directory",
)
SERVICES_OPTION = typer.Option(
    [],
    "--service",
    "-s",
    callback=comma_separated_list_callback,
    help="Select services (comma-separated or multiple -s arguments).",
)
PROFILES_OPTION = typer.Option(
    [],
    "--profile",
    "-p",
    callback=comma_separated_list_callback,
    help="Enable specific profiles (comma-separated or multiple -p arguments).",
)
ALL_PROFILES_OPTION = typer.Option(
    False,
    "--all",
    "-a",
    help="Select all profiles.",
)
RUNNING_OPTION = typer.Option(
    False, "--running", help="Consider only projects with at least one running or restarting service."
)
