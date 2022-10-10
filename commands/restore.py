import argparse
import dataclasses
import os

import rich
import rich.pretty
import rich.tree

from utils.backup_rich import list_backups
from utils.backup_rich import list_services
from utils.doco_config import load_doco_config
from utils.rich import format_cmd_line
from utils.rsync import run_rsync_download_incremental
from utils.rsync import run_rsync_list


@dataclasses.dataclass
class DownloadOptions:
    service: str
    backup: str
    dry_run: bool


def download_backup(options: DownloadOptions):
    doco_config = load_doco_config('.')
    destination = options.service
    if options.backup.isnumeric():
        _, file_list = run_rsync_list(doco_config.backup.rsync, target=f"{options.service}/",
                                      dry_run=False)
        backup_dir = sorted(
            [file for file in file_list if file.startswith('backup-')], reverse=True
        )[int(options.backup)]
    else:
        backup_dir = f"backup-{options.backup}"

    if not options.dry_run and os.path.exists(destination):
        if not os.path.isdir(destination):
            exit(f"Destination {destination} is not a directory.\n"
                 "Exiting.")
        answer = input(f"The directory {os.path.abspath(destination)} already exists.\n"
                       f"Enter '{options.service}' to overwrite (files may get deleted): ")
        if answer != options.service:
            exit('Cancelled.')

    cmd = run_rsync_download_incremental(doco_config.backup.rsync,
                                         source=f"{options.service}/{backup_dir}/",
                                         destination=f"{destination}/",
                                         dry_run=options.dry_run)

    if options.dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-s', '--service', nargs='?', help='target service to retrieve backups from')
    parser.add_argument('-l', '--list', action='store_true', help='list backups')
    parser.add_argument('-b', '--backup', default='0', help='backup index or name, default to 0')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually backup, only show what would be done')


def main(args) -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to load a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    if args.projects != ['.']:
        exit("You must not specify any project for restoring a backup.\n"
             "Exiting.")

    if args.list:
        if args.service is None:
            exit("You need to specify a service to get the backups from.\n"
                 "Exiting.")
        list_backups(service=args.service, dry_run=args.dry_run)
    else:
        if args.service is None:
            list_services(dry_run=args.dry_run)
        download_backup(DownloadOptions(
            service=args.service,
            backup=args.backup,
            dry_run=args.dry_run,
        ))

    return 0
