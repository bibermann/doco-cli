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
    follow: bool


def log_project(project: ComposeProject, options: Options, info: ProjectInfo):
    rich_run_compose(
        project.dir,
        project.file,
        command=[
            "logs",
            *(["-f"] if options.follow else []),
        ],
        dry_run=False,
        rich_node=info.run_node,
        cancelable=options.follow,
    )


def main(
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    running: bool = RUNNING_OPTION,
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow (adds -f)."),
):
    """
    Print logs of projects.
    """

    for project in get_compose_projects(
        projects,
        ProjectSearchOptions(
            print_compose_errors=False,
            only_running=running,
        ),
    ):
        do_project_cmd(
            # pylint: disable=cell-var-from-loop
            project=project,
            dry_run=False,
            cmd_task=lambda info: log_project(
                project,
                options=Options(
                    follow=follow,
                ),
                info=info,
            ),
        )
