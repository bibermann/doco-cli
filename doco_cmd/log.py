import argparse
import dataclasses

from utils.compose_rich import ComposeProject
from utils.compose_rich import get_compose_projects
from utils.compose_rich import ProjectSearchOptions
from utils.compose_rich import rich_run_compose
from utils.doco import do_project_cmd
from utils.doco import ProjectInfo


@dataclasses.dataclass
class Options:
    follow: bool


def log_project(project: ComposeProject, options: Options, info: ProjectInfo):
    rich_run_compose(
        project.dir, project.file,
        command=[
            'logs',
            *(['-f'] if options.follow else []),
        ],
        dry_run=False, rich_node=info.run_node, cancelable=options.follow,
    )


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-f', '--follow', action='store_true', help='follow (adds -f)')


def main(args) -> int:
    for project in get_compose_projects(args.projects, ProjectSearchOptions(
        print_compose_errors=False,
        only_running=args.running,
    )):
        do_project_cmd(
            project=project,
            dry_run=False,
            cmd_task=lambda info: log_project(project, options=Options(
                follow=args.follow,
            ), info=info)
        )

    return 0
