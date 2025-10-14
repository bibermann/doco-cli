import dataclasses
import pathlib

import typer

from src.utils.cli import ALL_PROFILES_OPTION
from src.utils.cli import PROFILES_OPTION
from src.utils.cli import PROJECTS_ARGUMENT
from src.utils.cli import RUNNING_OPTION
from src.utils.cli import SERVICES_OPTION
from src.utils.compose_rich import ComposeProject
from src.utils.compose_rich import get_compose_projects
from src.utils.compose_rich import ProjectSearchOptions
from src.utils.compose_rich import rich_run_compose
from src.utils.doco import do_project_cmd
from src.utils.doco import ProjectInfo


@dataclasses.dataclass
class Options:
    do_pull: bool
    do_log: bool
    show_timestamps: bool
    no_build: bool
    no_remove_orphans: bool
    dry_run: bool


def up_project(project: ComposeProject, options: Options, info: ProjectInfo):
    if not info.all_running:
        rich_run_compose(
            project.dir,
            project.file,
            project.selected_profiles,
            command=[
                "up",
                *(["--remove-orphans"] if not options.no_remove_orphans else []),
                *(["--build"] if not options.no_build else []),
                *(["--pull", "always"] if options.do_pull else []),
                "-d",
                *project.selected_services,
            ],
            dry_run=options.dry_run,
            cmds=info.cmds,
        )

    if options.do_log:
        rich_run_compose(
            project.dir,
            project.file,
            project.selected_profiles,
            command=[
                "logs",
                *(["-t"] if options.show_timestamps else []),
                "-f",
                *project.selected_services,
            ],
            dry_run=options.dry_run,
            cmds=info.cmds,
            cancelable=True,
        )


def main(  # noqa: CFQ002 (max arguments)
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    services: list[str] = SERVICES_OPTION,
    profiles: list[str] = PROFILES_OPTION,
    all_profiles: bool = ALL_PROFILES_OPTION,
    running: bool = RUNNING_OPTION,
    do_pull: bool = typer.Option(False, "--pull", help="Pull images before running."),
    do_log: bool = typer.Option(False, "--log", "-l", help="Also show logs."),
    show_timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Show timestamps in logs."),
    no_build: bool = typer.Option(False, "--no-build", help="Don't build images before running."),
    no_remove_orphans: bool = typer.Option(False, "--no-remove-orphans", help="Keep orphans."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually start anything, only show what would be done."
    ),
):
    """
    Start projects.
    """

    for project in get_compose_projects(
        projects,
        services,
        all_profiles or profiles,
        ProjectSearchOptions(
            print_compose_errors=dry_run,
            only_running=running,
        ),
    ):
        do_project_cmd(
            # pylint: disable=cell-var-from-loop
            project=project,
            dry_run=dry_run,
            cmd_task=lambda info: up_project(
                project,
                options=Options(
                    do_pull=do_pull,
                    do_log=do_log,
                    show_timestamps=show_timestamps,
                    no_build=no_build,
                    no_remove_orphans=no_remove_orphans,
                    dry_run=dry_run,
                ),
                info=info,
            ),
        )
