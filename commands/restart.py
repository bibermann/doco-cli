import argparse
import dataclasses

from utils.common import find_compose_projects
from utils.doco import do_project_cmd
from utils.doco import ProjectInfo
from utils.rich import rich_run_compose
from .down import DownOptions


@dataclasses.dataclass
class Options(DownOptions):
    dry_run: bool


def restart_project(compose_dir: str, compose_file: str, options: Options, info: ProjectInfo):
    if info.has_running_or_restarting or options.remove_volumes or options.force_down:
        rich_run_compose(
            compose_dir, compose_file,
            command=[
                'down',
                *(['-v'] if options.remove_volumes else []),
                *(['--remove-orphans'] if not options.no_remove_orphans else []),
            ],
            dry_run=options.dry_run, rich_node=info.run_node,
        )

    rich_run_compose(
        compose_dir, compose_file,
        command=['up', '--build', '-d'],
        dry_run=options.dry_run, rich_node=info.run_node,
    )


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-v', '--remove-volumes', action='store_true', help='remove volumes (adds -v)')
    parser.add_argument('-k', '--no-remove-orphans', action='store_true',
                        help='keep orphans (omits --remove-orphans)')
    parser.add_argument('-f', '--force', action='store_true', help='force calling down even if not running')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually start/stop anything, only show what would be done')


def main(args) -> int:
    for compose_dir, compose_file in find_compose_projects(args.projects):
        do_project_cmd(
            compose_dir=compose_dir,
            compose_file=compose_file,
            dry_run=args.dry_run,
            cmd_task=lambda info: restart_project(compose_dir, compose_file, options=Options(
                remove_volumes=args.remove_volumes,
                no_remove_orphans=args.no_remove_orphans,
                force_down=args.force,
                dry_run=args.dry_run,
            ), info=info)
        )

    return 0
