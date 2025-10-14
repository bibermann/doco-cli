import dataclasses
import pathlib

import typer

from .down import DownOptions
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
class Options(DownOptions):
    do_pull: bool
    do_log: bool
    show_timestamps: bool
    no_build: bool
    dry_run: bool


def restart_project(project: ComposeProject, options: Options, info: ProjectInfo):
    if info.has_running_or_restarting or options.remove_volumes or options.force_down:
        rich_run_compose(
            project.dir,
            project.file,
            project.selected_profiles,
            command=[
                "down",
                *(["--remove-orphans"] if not options.no_remove_orphans else []),
                *(["-v"] if options.remove_volumes else []),
                *project.selected_services,
            ],
            dry_run=options.dry_run,
            cmds=info.cmds,
        )

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
    remove_volumes: bool = typer.Option(
        False, "--remove-volumes", "-v", help="Remove volumes (implies -f / --force)."
    ),
    no_remove_orphans: bool = typer.Option(False, "--no-remove-orphans", help="Keep orphans."),
    force: bool = typer.Option(False, "--force", "-f", help="Force calling down even if not running."),
    do_pull: bool = typer.Option(False, "--pull", help="Pull images before running."),
    do_log: bool = typer.Option(False, "--log", "-l", help="Also show logs."),
    show_timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Show timestamps in logs."),
    no_build: bool = typer.Option(False, "--no-build", help="Don't build images before running."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually stop anything, only show what would be done."
    ),
):
    """
    Restart projects. This is like [i]down[/] and [i]up[/] in one command.
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
            project=project,
            dry_run=dry_run,
            cmd_task=lambda info: restart_project(
                # pylint: disable=cell-var-from-loop
                project,
                options=Options(
                    remove_volumes=remove_volumes,
                    no_remove_orphans=no_remove_orphans,
                    force_down=force,
                    do_pull=do_pull,
                    do_log=do_log,
                    show_timestamps=show_timestamps,
                    no_build=no_build,
                    dry_run=dry_run,
                ),
                info=info,
            ),
        )
