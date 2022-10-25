import argparse

from utils.doco_config import DocoConfig
from utils.restore_rich import list_backups
from utils.restore_rich import list_projects


def add_to_parser(parser: argparse.ArgumentParser):
    pass


def main(args, doco_config: DocoConfig) -> int:
    if args.project is None:
        list_projects(doco_config=doco_config)
    else:
        list_backups(project_name=args.project, doco_config=doco_config)

    return 0
