import argparse
import dataclasses
import os
import typing as t

from utils.backup_rich import list_backups
from utils.backup_rich import list_projects
from utils.compose_rich import ComposeProject
from utils.compose_rich import get_compose_projects
from utils.compose_rich import ProjectSearchOptions


@dataclasses.dataclass
class RestoreOptions:
    project_name: t.Optional[str]
    backup: str
    live: bool
    dry_run: bool
    dry_run_verbose: bool


def restore_project(project: ComposeProject, options: RestoreOptions):
    print("restoring project")


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-p', '--project', nargs='?',
                        help='target projects to retrieve backups from; using directory name if empty')
    parser.add_argument('-l', '--list', action='store_true', help='list backups')
    parser.add_argument('-b', '--backup', default='0', help='backup index or name, default to 0')
    parser.add_argument('--live', action='store_true', help='do not stop the services before backup')
    parser.add_argument('--verbose', action='store_true', help='print more details if --dry-run')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually restore a backup, only show what would be done')


def main(args) -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to restore a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    projects = list(get_compose_projects(args.projects, ProjectSearchOptions(
        print_compose_errors=args.dry_run,
        only_running=args.running,
        allow_empty=True,
    )))

    if args.project is not None and len(projects) != 1:
        exit("You cannot specify --project when restoring more than one project.\n"
             "Exiting.")

    if args.list:
        for project in projects:
            list_backups(project_name=project.config['name'] if args.project is None else args.project,
                         dry_run=args.dry_run)
    elif len(projects) == 0:
        list_projects(dry_run=args.dry_run)
    else:
        for project in projects:
            restore_project(
                project=project,
                options=RestoreOptions(
                    project_name=args.project,
                    backup=args.backup,
                    live=args.live,
                    dry_run=args.dry_run,
                    dry_run_verbose=args.verbose,
                )
            )

    return 0
