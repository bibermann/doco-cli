import argparse
import dataclasses
import itertools
import json
import os
import tempfile
import typing as t

import rich.json
import rich.panel
import rich.tree

from utils.compose_rich import ComposeProject
from utils.compose_rich import get_compose_projects
from utils.compose_rich import ProjectSearchOptions
from utils.compose_rich import rich_run_compose
from utils.doco_config import load_doco_config
from utils.restore import create_target_structure
from utils.restore import do_restore_job
from utils.restore import get_backup_directory
from utils.restore import RestoreJob
from utils.restore_rich import list_backups
from utils.restore_rich import list_projects
from utils.rich import Formatted
from utils.rsync import run_rsync_download_incremental


@dataclasses.dataclass
class RestoreOptions:
    project_name: t.Optional[str]
    backup: str
    dry_run: bool
    dry_run_verbose: bool


@dataclasses.dataclass
class RestoreConfigTasks:
    restart_project: bool = False


@dataclasses.dataclass
class RestoreConfig:
    tasks: RestoreConfigTasks


def do_restore(project: ComposeProject, options: RestoreOptions, config: RestoreConfig,
               jobs: list[RestoreJob],
               run_node: rich.tree.Tree):
    create_target_structure(jobs=jobs, dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.restart_project:
        rich_run_compose(project.dir, project.file,
                         command=['down'],
                         dry_run=options.dry_run, rich_node=run_node)

    for job in jobs:
        do_restore_job(rsync_config=project.doco_config.backup.rsync,
                       job=job,
                       dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.restart_project:
        rich_run_compose(project.dir, project.file,
                         command=['up', '-d'],
                         dry_run=options.dry_run, rich_node=run_node)


def restore_project(project: ComposeProject, options: RestoreOptions):
    backup_dir = get_backup_directory(project.doco_config.backup.rsync,
                                      project_name=options.project_name,
                                      backup_id=options.backup)

    backup_config: any = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, 'config.json')
        run_rsync_download_incremental(project.doco_config.backup.rsync,
                                       source=f"{options.project_name}/{backup_dir}/config.json",
                                       destination=os.path.join(tmp_dir, 'config.json'),
                                       dry_run=False)
        with open(config_path, encoding='utf-8') as f:
            backup_config = json.load(f)

    project_name = options.project_name
    project_id = f"[b]{Formatted(project_name)}[/]"
    project_id += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"
    project_id = Formatted(project_id, True)

    tree = rich.tree.Tree(str(project_id))
    backup_dir_node = tree.add(f"[i]Backup directory:[/] [b]{Formatted(backup_dir)}[/]")
    backup_node = tree.add('[i]Backup items[/]')

    backup_volumes = list(itertools.chain(*[service.get('backup_volumes', []) for service in
                                            backup_config.get('tasks', {}).get('backup_services', [])]))

    has_running_or_restarting = False
    for service_name, service in project.config.get('services', {}).items():
        state = next((s['State'] for s in project.ps if s['Service'] == service_name), 'exited')
        if state in ['running', 'restarting']:
            has_running_or_restarting = True

    config = RestoreConfig(
        tasks=RestoreConfigTasks(),
    )
    jobs: list[RestoreJob] = []

    backup_project_dir = backup_config.get('tasks', {}).get('backup_project_dir', True)
    if backup_project_dir:
        jobs.append(RestoreJob(
            source_path='project_files' if type(backup_project_dir) == bool else backup_project_dir[1],
            target_path='.' if type(backup_project_dir) == bool else backup_project_dir[0],
            project_dir=project.dir))

    for backup_volumes_item in backup_volumes:
        jobs.append(RestoreJob(source_path=backup_volumes_item[1], target_path=backup_volumes_item[0],
                               project_dir=project.dir))

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

    config.tasks.restart_project = has_running_or_restarting

    do_restore(project=project, options=options, config=config, jobs=jobs, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group = rich.console.Group('[green]config.json[/]')
            backup_dir_node.add(config_group)

            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(json.dumps(backup_config, indent=4)),
                                 expand=False,
                                 border_style='green')
            )

        rich.print(tree)


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-p', '--project', nargs='?',
                        help='target projects to retrieve backups from; using directory name if empty')
    parser.add_argument('-l', '--list', action='store_true', help='list backups')
    parser.add_argument('-b', '--backup', default='0', help='backup index or name, defaults to 0')
    parser.add_argument('--verbose', action='store_true', help='print more details if --dry-run')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually restore a backup, only show what would be done')


def main(args) -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to restore a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    projects = list(get_compose_projects(args.projects, ProjectSearchOptions(
        print_compose_errors=args.dry_run,
        only_running=args.running,
        allow_empty=True,
    )))

    if args.project is not None and len(projects) != 1:
        exit("You cannot specify --project when restoring more than one project.\n"
             "Exiting.")

    if args.list:
        for project in projects:
            list_backups(project_name=project.config['name'] if args.project is None else args.project,
                         dry_run=args.dry_run,
                         doco_config=project.doco_config)
    elif len(projects) == 0:
        list_projects(dry_run=args.dry_run,
                      doco_config=load_doco_config('.'))
    else:
        for project in projects:
            restore_project(
                project=project,
                options=RestoreOptions(
                    project_name=project.config['name'] if args.project is None else args.project,
                    backup=args.backup,
                    dry_run=args.dry_run,
                    dry_run_verbose=args.verbose,
                )
            )

    return 0
