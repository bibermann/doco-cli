import argparse

from utils.doco_config import DocoConfig
from utils.restore_rich import list_backups
from utils.restore_rich import list_projects


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually list, only show what would be done')


def main(args, doco_config: DocoConfig) -> int:
    if args.project is None:
        list_projects(dry_run=args.dry_run, doco_config=doco_config)
    else:
        list_backups(project_name=args.project, dry_run=args.dry_run, doco_config=doco_config)

    return 0
