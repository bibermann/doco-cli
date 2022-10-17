#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import os
import sys

import argcomplete

import bbak_commands.backup
import bbak_commands.get_backup
import bbak_commands.list
from utils.doco_config import load_doco_config

# import bbak_commands.restore

LIST_COMMAND = 'ls'
BACKUP_COMMAND = 'backup'
GET_BACKUP_COMMAND = 'get'
RESTORE_COMMAND = 'restore'


def main() -> int:
    main_parser = argparse.ArgumentParser()
    parser = main_parser

    parser.add_argument('-w', '--workdir', default='.', help='change working directory')
    parser.add_argument('-r', '--root', nargs='?', help='change root')
    parser.add_argument('-p', '--project', nargs='?', help='target project to retrieve backups from')

    subparsers = parser.add_subparsers(dest='command')

    bbak_commands.list.add_to_parser(subparsers.add_parser(LIST_COMMAND, help='list'))
    bbak_commands.backup.add_to_parser(subparsers.add_parser(BACKUP_COMMAND, help='backup'))
    bbak_commands.get_backup.add_to_parser(
        subparsers.add_parser(GET_BACKUP_COMMAND, help='get backup for local analysis'))
    # bbak_commands.restore.add_to_parser(subparsers.add_parser(RESTORE_COMMAND, help='restore a backup'))

    argcomplete.autocomplete(main_parser)
    args = main_parser.parse_args()

    if args.project is not None:
        if args.project.endswith('/'):
            args.project = args.project[:-1]
        if '/' in args.project or args.project == '.' or args.project == '':
            exit("Project name is invalid.\n"
                 "Please check your -p argument. Exiting.")

    doco_config = load_doco_config(args.workdir)
    if args.root is not None:
        doco_config.backup.rsync.root = \
            os.path.normpath(os.path.join(doco_config.backup.rsync.root, args.root))

    if args.command == LIST_COMMAND:
        bbak_commands.list.main(args, doco_config)
    elif args.command == BACKUP_COMMAND:
        bbak_commands.backup.main(args, doco_config)
    elif args.command == GET_BACKUP_COMMAND:
        bbak_commands.get_backup.main(args, doco_config)
    # elif args.command == RESTORE_COMMAND:
    #     bbak_commands.restore.main(args, doco_config)

    return 0


if __name__ == '__main__':
    sys.exit(main())
