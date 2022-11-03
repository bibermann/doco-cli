import dataclasses
import pathlib

import typer

from .down import DownOptions
from src.utils.cli import PROJECTS_ARGUMENT
from src.utils.cli import RUNNING_OPTION
from src.utils.compose_rich import ComposeProject
from src.utils.compose_rich import get_compose_projects
from src.utils.compose_rich import ProjectSearchOptions
from src.utils.compose_rich import rich_run_compose
from src.utils.doco import do_project_cmd
from src.utils.doco import ProjectInfo


@dataclasses.dataclass
class Options(DownOptions):
    do_log: bool
    dry_run: bool


def restart_project(project: ComposeProject, options: Options, info: ProjectInfo):
    if info.has_running_or_restarting or options.remove_volumes or options.force_down:
        rich_run_compose(
            project.dir,
            project.file,
            command=[
                "down",
                *(["-v"] if options.remove_volumes else []),
                *(["--remove-orphans"] if not options.no_remove_orphans else []),
            ],
            dry_run=options.dry_run,
            rich_node=info.run_node,
        )

    rich_run_compose(
        project.dir,
        project.file,
        command=["up", "--build", "-d"],
        dry_run=options.dry_run,
        rich_node=info.run_node,
    )

    if options.do_log:
        rich_run_compose(
            project.dir,
            project.file,
            command=["logs", "-f"],
            dry_run=options.dry_run,
            rich_node=info.run_node,
            cancelable=True,
        )


def main(  # noqa: CFQ002 (max arguments)
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    running: bool = RUNNING_OPTION,
    remove_volumes: bool = typer.Option(False, "--remove-volumes", "-v", help="Remove volumes (adds -v)."),
    no_remove_orphans: bool = typer.Option(
        False, "--no-remove-orphans", "-k", help="Keep orphans (omits --remove-orphans)."
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force calling down even if not running."),
    do_log: bool = typer.Option(False, "--log", "-l", help="Also show logs."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually stop anything, only show what would be done."
    ),
):
    """
    Restart projects. This is like [i]down[/] and [i]up[/] in one command.
    """

    for project in get_compose_projects(
        projects,
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
                    do_log=do_log,
                    dry_run=dry_run,
                ),
                info=info,
            ),
        )
