#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import os
import sys

import argcomplete

import doco_cmd.backup
import doco_cmd.down
import doco_cmd.log
import doco_cmd.restart
import doco_cmd.restore
import doco_cmd.status
import doco_cmd.up
from utils.system import get_user_groups

STATUS_COMMAND = 's'
RESTART_COMMAND = 'r'
DOWN_COMMAND = 'd'
UP_COMMAND = 'u'
LOG_COMMAND = 'l'
BACKUP_COMMAND = 'backup'
RESTORE_COMMAND = 'restore'


def main() -> int:
    if not (os.geteuid() == 0 or 'docker' in get_user_groups()):
        exit("You need to belong to the docker group or have root privileges to run this script.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    main_parser = argparse.ArgumentParser()
    parser = main_parser

    parser.add_argument('projects', nargs='*', default=['.'],
                        help='compose files and/or directories containing a docker-compose.y[a]ml')
    parser.add_argument('--running', action='store_true',
                        help='consider only projects with at least one running or restarting service')

    subparsers = parser.add_subparsers(dest='command')

    doco_cmd.status.add_to_parser(subparsers.add_parser(STATUS_COMMAND, help='status'))
    doco_cmd.restart.add_to_parser(subparsers.add_parser(RESTART_COMMAND, help='restart (down and up)'))
    doco_cmd.down.add_to_parser(subparsers.add_parser(DOWN_COMMAND, help='down'))
    doco_cmd.up.add_to_parser(subparsers.add_parser(UP_COMMAND, help='up'))
    doco_cmd.log.add_to_parser(subparsers.add_parser(LOG_COMMAND, help='log'))
    doco_cmd.backup.add_to_parser(subparsers.add_parser(BACKUP_COMMAND, help='backup'))
    doco_cmd.restore.add_to_parser(subparsers.add_parser(RESTORE_COMMAND, help='restore a backup'))

    argcomplete.autocomplete(main_parser)
    args = main_parser.parse_args()

    if args.command == STATUS_COMMAND:
        doco_cmd.status.main(args)
    elif args.command == RESTART_COMMAND:
        doco_cmd.restart.main(args)
    elif args.command == DOWN_COMMAND:
        doco_cmd.down.main(args)
    elif args.command == UP_COMMAND:
        doco_cmd.up.main(args)
    elif args.command == LOG_COMMAND:
        doco_cmd.log.main(args)
    elif args.command == BACKUP_COMMAND:
        doco_cmd.backup.main(args)
    elif args.command == RESTORE_COMMAND:
        doco_cmd.restore.main(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
