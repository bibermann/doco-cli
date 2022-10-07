import argparse
import dataclasses

from utils.doco import do_project_cmd
from utils.doco import ProjectInfo
from utils.rich import ComposeProject
from utils.rich import get_compose_projects
from utils.rich import rich_run_compose


@dataclasses.dataclass
class Options:
    dry_run: bool


def up_project(project: ComposeProject, options: Options, info: ProjectInfo):
    if not info.all_running:
        rich_run_compose(
            project.dir, project.file,
            command=['up', '--build', '-d'],
            dry_run=options.dry_run, rich_node=info.run_node,
        )


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually start anything, only show what would be done')


def main(args) -> int:
    for project in get_compose_projects(args.projects):
        do_project_cmd(
            project=project,
            dry_run=args.dry_run,
            cmd_task=lambda info: up_project(project, options=Options(
                dry_run=args.dry_run,
            ), info=info)
        )

    return 0
