#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import argparse
import sys

import argcomplete

import commands.status
import commands.restart
import commands.down
import commands.up
import commands.log

STATUS_COMMAND = 's'
RESTART_COMMAND = 'r'
DOWN_COMMAND = 'd'
UP_COMMAND = 'u'
LOG_COMMAND = 'l'


def main() -> int:
    main_parser = argparse.ArgumentParser()
    parser = main_parser

    parser.add_argument('projects', nargs='*', default=['.'],
                        help='compose files and/or directories containing a docker-compose.y[a]ml')

    subparsers = parser.add_subparsers(dest='command')

    commands.status.add_to_parser(subparsers.add_parser(STATUS_COMMAND, help='status'))
    commands.restart.add_to_parser(subparsers.add_parser(RESTART_COMMAND, help='restart (down and up)'))
    commands.down.add_to_parser(subparsers.add_parser(DOWN_COMMAND, help='down'))
    commands.up.add_to_parser(subparsers.add_parser(UP_COMMAND, help='up'))
    commands.log.add_to_parser(subparsers.add_parser(LOG_COMMAND, help='log'))

    argcomplete.autocomplete(main_parser)
    args = main_parser.parse_args()

    if args.command == STATUS_COMMAND:
        commands.status.main(args)
    elif args.command == RESTART_COMMAND:
        commands.restart.main(args)
    elif args.command == DOWN_COMMAND:
        commands.down.main(args)
    elif args.command == UP_COMMAND:
        commands.up.main(args)
    elif args.command == LOG_COMMAND:
        commands.log.main(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
