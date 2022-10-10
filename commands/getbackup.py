import argparse
import dataclasses
import os

import rich
import rich.pretty
import rich.tree

from utils.backup import get_backup_directory
from utils.backup_rich import list_backups
from utils.backup_rich import list_projects
from utils.doco_config import load_doco_config
from utils.rich import format_cmd_line
from utils.rsync import run_rsync_download_incremental


@dataclasses.dataclass
class DownloadOptions:
    project_name: str
    backup: str
    destination: str
    dry_run: bool


def download_backup(options: DownloadOptions):
    doco_config = load_doco_config('.')
    backup_dir = get_backup_directory(doco_config.backup.rsync,
                                      project_name=options.project_name,
                                      backup_id=options.backup)

    if not options.dry_run and os.path.exists(options.destination):
        if not os.path.isdir(options.destination):
            exit(f"Destination {options.destination} is not a directory.\n"
                 "Exiting.")
        answer = input(f"The directory {os.path.abspath(options.destination)} already exists.\n"
                       f"Enter '{options.destination}' to overwrite (files may get deleted): ")
        if answer != options.destination:
            exit('Cancelled.')

    cmd = run_rsync_download_incremental(doco_config.backup.rsync,
                                         source=f"{options.project_name}/{backup_dir}/",
                                         destination=f"{options.destination}/",
                                         dry_run=options.dry_run)

    if options.dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-p', '--project', nargs='?', help='target project to retrieve backups from')
    parser.add_argument('-l', '--list', action='store_true', help='list backups')
    parser.add_argument('-b', '--backup', default='0', help='backup index or name, defaults to 0')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually backup, only show what would be done')


def main(args) -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to load a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    if len(args.projects != 1):
        exit("You must specify a project directory to load the backup to.\n"
             "Exiting.")

    if args.running:
        exit("--running is not supported for loading a backup.\n"
             "Exiting.")

    if args.list:
        if args.project is None:
            exit("You need to specify a project to get the backups from.\n"
                 "Exiting.")
        list_backups(project_name=args.project, dry_run=args.dry_run)
    elif args.project is None:
        list_projects(dry_run=args.dry_run)
    else:
        download_backup(DownloadOptions(
            project_name=args.project,
            backup=args.backup,
            destination=args.projects[0],
            dry_run=args.dry_run,
        ))

    return 0
