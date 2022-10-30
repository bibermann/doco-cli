import dataclasses
import pathlib

import typer

from src.utils.cli import PROJECTS_ARGUMENT
from src.utils.cli import RUNNING_OPTION
from src.utils.compose_rich import ComposeProject
from src.utils.compose_rich import get_compose_projects
from src.utils.compose_rich import ProjectSearchOptions
from src.utils.compose_rich import rich_run_compose
from src.utils.doco import do_project_cmd
from src.utils.doco import ProjectInfo


@dataclasses.dataclass
class Options:
    dry_run: bool


def up_project(project: ComposeProject, options: Options, info: ProjectInfo):
    if not info.all_running:
        rich_run_compose(
            project.dir,
            project.file,
            command=["up", "--build", "-d"],
            dry_run=options.dry_run,
            rich_node=info.run_node,
        )


def main(
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    running: bool = RUNNING_OPTION,
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually start anything, only show what would be done."
    ),
):
    """
    Start projects.
    """

    for project in get_compose_projects(
        projects,
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
                    dry_run=dry_run,
                ),
                info=info,
            ),
        )
