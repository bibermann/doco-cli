import argparse
import dataclasses

from utils.common import find_compose_projects
from utils.doco import do_project_cmd
from utils.doco import ProjectInfo
from utils.rich import rich_run_compose


@dataclasses.dataclass
class Options:
    follow: bool
    dry_run: bool


def restart_project(compose_dir: str, compose_file: str, options: Options, info: ProjectInfo):
    rich_run_compose(
        compose_dir, compose_file,
        command=[
            'logs',
            *(['-f'] if options.follow else []),
        ],
        dry_run=options.dry_run, rich_node=info.run_node, cancelable=options.follow,
    )


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-f', '--follow', action='store_true', help='follow (adds -f)')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually call log, only show what would be done')


def main(args) -> int:
    for compose_dir, compose_file in find_compose_projects(args.projects):
        do_project_cmd(
            compose_dir=compose_dir,
            compose_file=compose_file,
            dry_run=args.dry_run,
            cmd_task=lambda info: restart_project(compose_dir, compose_file, options=Options(
                follow=args.follow,
                dry_run=args.dry_run,
            ), info=info)
        )

    return 0
