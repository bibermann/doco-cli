import argparse
import dataclasses
import json
import os
import tempfile

import rich.json
import rich.panel
import rich.tree

from utils.backup import BACKUP_CONFIG_JSON
from utils.doco_config import DocoConfig
from utils.restore_rich import create_target_structure
from utils.restore_rich import do_restore_job
from utils.restore import get_backup_directory
from utils.restore import RestoreJob
from utils.rich import Formatted
from utils.rich import rich_print_cmd
from utils.rsync import run_rsync_download_incremental


@dataclasses.dataclass
class RestoreOptions:
    workdir: str
    backup: str
    dry_run: bool
    dry_run_verbose: bool


def do_restore(options: RestoreOptions, jobs: list[RestoreJob],
               doco_config: DocoConfig, run_node: rich.tree.Tree):
    create_target_structure(jobs=jobs, dry_run=options.dry_run, rich_node=run_node)

    for job in jobs:
        do_restore_job(rsync_config=doco_config.backup.rsync,
                       job=job,
                       dry_run=options.dry_run, rich_node=run_node)


def restore_files(project_name: str, options: RestoreOptions, doco_config: DocoConfig):
    backup_dir = get_backup_directory(doco_config.backup.rsync,
                                      project_name=project_name,
                                      backup_id=options.backup,
                                      print_cmd_callback=rich_print_cmd)

    backup_config: any = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, BACKUP_CONFIG_JSON)
        run_rsync_download_incremental(doco_config.backup.rsync,
                                       source=f"{project_name}/{backup_dir}/{BACKUP_CONFIG_JSON}",
                                       destination=os.path.join(tmp_dir, BACKUP_CONFIG_JSON),
                                       dry_run=False,
                                         print_cmd_callback=rich_print_cmd)
        with open(config_path, encoding='utf-8') as f:
            backup_config = json.load(f)

    project_id = f"[b]{Formatted(project_name)}[/]"

    tree = rich.tree.Tree(str(project_id))
    backup_dir_node = tree.add(f"[i]Backup directory:[/] [b]{Formatted(backup_dir)}[/]")

    if backup_config.get('backup_tool', '') != 'bbak':
        config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
        backup_dir_node.add(config_group)

        config_group.renderables.append(
            rich.panel.Panel(rich.json.JSON(json.dumps(backup_config, indent=4)),
                             expand=False,
                             border_style='green')
        )

        tree.add('[red][b]Error:[/] The config does not look like a bbak config.[/]')
        rich.print(tree)
        exit(1)

    backup_node = tree.add('[i]Backup items[/]')

    backup_paths = backup_config.get('tasks', {}).get('backup_paths', [])

    jobs: list[RestoreJob] = []

    for backup_paths_item in backup_paths:
        jobs.append(RestoreJob(source_path=backup_paths_item[1], target_path=backup_paths_item[0],
                               project_dir=options.workdir))

    for job in jobs:
        if os.path.exists(job.absolute_target_path):
            action = '[red](override)[/]'
        else:
            action = '(create)'
        backup_node.add(
            f"{job.display_source_path} [dim]->[/] [dark_orange]{job.display_target_path}[/] {action}")

    run_node = rich.tree.Tree('[i]Would run[/]')
    if options.dry_run_verbose:
        tree.add(run_node)

    do_restore(options=options, jobs=jobs, doco_config=doco_config, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
            backup_dir_node.add(config_group)

            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(json.dumps(backup_config, indent=4)),
                                 expand=False,
                                 border_style='green')
            )

        rich.print(tree)


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-b', '--backup', default='0', help='backup index or name, defaults to 0')
    parser.add_argument('--verbose', action='store_true', help='print more details if --dry-run')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually restore a backup, only show what would be done')


def main(args, doco_config: DocoConfig) -> int:
    if not (args.dry_run or os.geteuid() == 0):
        exit("You need to have root privileges to restore a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    if args.project is None:
        exit("You must specify --project for 'restore' command.\n"
             "Exiting.")

    restore_files(
        project_name=args.project,
        options=RestoreOptions(
            workdir=args.workdir,
            backup=args.backup,
            dry_run=args.dry_run,
            dry_run_verbose=args.verbose,
        ),
        doco_config=doco_config,
    )

    return 0
