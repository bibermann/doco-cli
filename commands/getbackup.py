import argparse
import dataclasses
import os
import typing as t

import rich
import rich.pretty
import rich.tree

from utils.doco_config import load_doco_config
from utils.rich import format_cmd_line
from utils.rich import Formatted
from utils.rsync import run_rsync_download_incremental
from utils.rsync import run_rsync_list


@dataclasses.dataclass
class ListOptions:
    service: t.Optional[str]
    dry_run: bool


@dataclasses.dataclass
class DownloadOptions(ListOptions):
    backup: str
    destination: str


def list_services(options: ListOptions):
    doco_config = load_doco_config('.')
    cmd, file_list = run_rsync_list(doco_config.backup.rsync, target="", dry_run=options.dry_run)
    if options.dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))
    else:
        tree = rich.tree.Tree(f"[b]Services[/]")
        files = sorted([file for file in file_list if file != '.'])
        for i, file in enumerate(files):
            tree.add(f"[yellow]{Formatted(file)}[/]")
        rich.print(tree)


def list_backups(options: ListOptions):
    doco_config = load_doco_config('.')
    cmd, file_list = run_rsync_list(doco_config.backup.rsync, target=f"{options.service}/",
                                    dry_run=options.dry_run)
    if options.dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))
    else:
        tree = rich.tree.Tree(f"[b]{Formatted(options.service)}[/]")
        files = sorted([file[7:] for file in file_list if file.startswith('backup-')], reverse=True)
        for i, file in enumerate(files):
            tree.add(f"[yellow]{i}[/][dim]:[/] {Formatted(file)}")
        rich.print(tree)


def download_backup(options: DownloadOptions):
    doco_config = load_doco_config('.')
    if options.backup.isnumeric():
        _, file_list = run_rsync_list(doco_config.backup.rsync, target=f"{options.service}/",
                                      dry_run=False)
        backup_dir = sorted(
            [file for file in file_list if file.startswith('backup-')], reverse=True
        )[int(options.backup)]
    else:
        backup_dir = f"backup-{options.backup}"

    if not options.dry_run and os.path.exists(options.destination):
        if not os.path.isdir(options.destination):
            exit(f"Destination {options.destination} is not a directory.\n"
                 "Exiting.")
        answer = input(f"The directory {os.path.abspath(options.destination)} already exists.\n"
                       f"Enter '{options.destination}' to overwrite (files may get deleted): ")
        if answer != options.destination:
            exit('Cancelled.')

    cmd = run_rsync_download_incremental(doco_config.backup.rsync,
                                         source=f"{options.service}/{backup_dir}/",
                                         destination=f"{options.destination}/",
                                         dry_run=options.dry_run)

    if options.dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-s', '--service', nargs='?', help='target service to retrieve backups from')
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

    if args.list:
        if args.service is None:
            exit("You need to specify a service to get the backups from.\n"
                 "Exiting.")
        list_backups(ListOptions(service=args.service, dry_run=args.dry_run))
    else:
        if args.service is None:
            list_services(ListOptions(service=None, dry_run=args.dry_run))
        download_backup(DownloadOptions(
            service=args.service,
            backup=args.backup,
            destination=args.projects[0],
            dry_run=args.dry_run,
        ))

    return 0
