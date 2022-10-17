import argparse
import dataclasses
import os

import rich
import rich.pretty
import rich.tree

from utils.doco_config import DocoConfig
from utils.restore import get_backup_directory
from utils.rich import format_cmd_line
from utils.rsync import run_rsync_download_incremental


@dataclasses.dataclass
class DownloadOptions:
    project_name: str
    backup: str
    destination: str
    dry_run: bool


def download_backup(options: DownloadOptions, doco_config: DocoConfig):
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
    parser.add_argument('-b', '--backup', default='0', help='backup index or name, defaults to 0')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually backup, only show what would be done')


def main(args, doco_config: DocoConfig) -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to load a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    if args.project is None:
        exit("You must specify --project for 'get' command.\n"
             "Exiting.")

    download_backup(
        DownloadOptions(
            project_name=args.project,
            backup=args.backup,
            destination=os.path.join(args.workdir, args.project),
            dry_run=args.dry_run,
        ),
        doco_config=doco_config,
    )

    return 0
