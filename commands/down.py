import argparse
import dataclasses

from utils.compose_rich import ComposeProject
from utils.compose_rich import get_compose_projects
from utils.compose_rich import rich_run_compose
from utils.doco import do_project_cmd
from utils.doco import ProjectInfo
from utils.rich import ProjectSearchOptions


@dataclasses.dataclass
class DownOptions:
    remove_volumes: bool
    no_remove_orphans: bool
    force_down: bool


@dataclasses.dataclass
class Options(DownOptions):
    dry_run: bool


def down_project(project: ComposeProject, options: Options, info: ProjectInfo):
    if info.has_running_or_restarting or options.remove_volumes or options.force_down:
        rich_run_compose(
            project.dir, project.file,
            command=[
                'down',
                *(['-v'] if options.remove_volumes else []),
                *(['--remove-orphans'] if not options.no_remove_orphans else []),
            ],
            dry_run=options.dry_run, rich_node=info.run_node,
        )


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-v', '--remove-volumes', action='store_true', help='remove volumes (adds -v)')
    parser.add_argument('-k', '--no-remove-orphans', action='store_true',
                        help='keep orphans (omits --remove-orphans)')
    parser.add_argument('-f', '--force', action='store_true', help='force calling down even if not running')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually stop anything, only show what would be done')


def main(args) -> int:
    for project in get_compose_projects(args.projects, ProjectSearchOptions(only_running=args.running)):
        do_project_cmd(
            project=project,
            dry_run=args.dry_run,
            cmd_task=lambda info: down_project(project, options=Options(
                remove_volumes=args.remove_volumes,
                no_remove_orphans=args.no_remove_orphans,
                force_down=args.force,
                dry_run=args.dry_run,
            ), info=info)
        )

    return 0
