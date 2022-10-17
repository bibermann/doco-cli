import argparse
import dataclasses
import datetime
import os
import re
import typing as t

import pydantic
import rich
import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from utils.backup import BACKUP_CONFIG_JSON
from utils.backup import BackupJob
from utils.backup import create_target_structure
from utils.backup import do_backup_content
from utils.backup import do_backup_job
from utils.backup import LAST_BACKUP_DIR_FILENAME
from utils.backup import load_last_backup_directory
from utils.backup import save_last_backup_directory
from utils.backup_rich import format_do_backup
from utils.backup_rich import format_no_backup
from utils.common import dir_from_path
from utils.common import relative_path_if_below
from utils.compose_rich import ComposeProject
from utils.compose_rich import get_compose_projects
from utils.compose_rich import ProjectSearchOptions
from utils.compose_rich import rich_run_compose
from utils.rich import Formatted
from utils.rsync import RsyncConfig

COMPOSE_CONFIG_YAML = 'compose.yaml'


@dataclasses.dataclass
class BackupOptions:
    include_project_dir: bool
    include_read_only_volumes: bool
    volumes: list[str]
    live: bool
    dry_run: bool
    dry_run_verbose: bool


class BackupConfigServiceTask(pydantic.BaseModel):
    name: str
    backup_volumes: list[t.Tuple[str, str]] = []
    exclude_volumes: list[str] = []


class BackupConfigOptions(pydantic.BaseModel):
    live: bool
    include_project_dir: bool
    include_read_only_volumes: bool
    volume_patterns: list[str]


class BackupConfigTasks(pydantic.BaseModel):
    restart_project: bool = False
    create_last_backup_dir_file: t.Union[bool, str]
    backup_config: t.Union[bool, str]
    backup_compose_config: t.Union[bool, str]
    backup_project_dir: t.Union[bool, t.Tuple[str, str]]
    backup_services: list[BackupConfigServiceTask] = []


class BackupConfig(pydantic.BaseModel):
    backup_tool: str = 'doco'
    project_path: str
    compose_file: str
    timestamp: datetime.datetime
    backup_dir: str
    last_backup_dir: t.Optional[str]
    rsync: RsyncConfig
    options: BackupConfigOptions
    tasks: BackupConfigTasks


def do_backup(project: ComposeProject, options: BackupOptions, config: BackupConfig, jobs: list[BackupJob],
              run_node: rich.tree.Tree):
    create_target_structure(rsync_config=project.doco_config.backup.rsync,
                            new_backup_dir=config.backup_dir, jobs=jobs, dry_run=options.dry_run,
                            rich_node=run_node)

    if config.tasks.restart_project:
        rich_run_compose(project.dir, project.file,
                         command=['down'],
                         dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.backup_config:
        do_backup_content(rsync_config=project.doco_config.backup.rsync,
                          new_backup_dir=config.backup_dir, old_backup_dir=config.last_backup_dir,
                          content=config.json(indent=4),
                          target_file_name=BACKUP_CONFIG_JSON,
                          dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.backup_compose_config:
        do_backup_content(rsync_config=project.doco_config.backup.rsync,
                          new_backup_dir=config.backup_dir, old_backup_dir=config.last_backup_dir,
                          content=project.config_yaml,
                          target_file_name=COMPOSE_CONFIG_YAML,
                          dry_run=options.dry_run, rich_node=run_node)

    for job in jobs:
        do_backup_job(rsync_config=project.doco_config.backup.rsync,
                      new_backup_dir=config.backup_dir, old_backup_dir=config.last_backup_dir, job=job,
                      dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.restart_project:
        rich_run_compose(project.dir, project.file,
                         command=['up', '-d'],
                         dry_run=options.dry_run, rich_node=run_node)

    if not options.dry_run and config.tasks.create_last_backup_dir_file:
        save_last_backup_directory(project.dir, config.backup_dir)


def backup_project(project: ComposeProject, options: BackupOptions):
    project_name = project.config['name']
    project_id = f"[b]{Formatted(project_name)}[/]"
    project_id += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"
    project_id = Formatted(project_id, True)

    now = datetime.datetime.now()
    new_backup_dir = os.path.join(project_name, f"backup-{now.strftime('%Y-%m-%d_%H.%M')}")
    old_backup_dir = load_last_backup_directory(project.dir)

    config = BackupConfig(
        project_path=os.path.abspath(project.dir),
        compose_file=project.file,
        timestamp=now,
        backup_dir=new_backup_dir,
        last_backup_dir=old_backup_dir,
        rsync=project.doco_config.backup.rsync,
        options=BackupConfigOptions(
            live=options.live,
            include_project_dir=options.include_project_dir,
            include_read_only_volumes=options.include_read_only_volumes,
            volume_patterns=options.volumes,
        ),
        tasks=BackupConfigTasks(
            create_last_backup_dir_file=LAST_BACKUP_DIR_FILENAME,
            backup_config=BACKUP_CONFIG_JSON,
            backup_compose_config=COMPOSE_CONFIG_YAML,
            backup_project_dir=options.include_project_dir,
        ),
    )
    jobs: list[BackupJob] = []

    tree = rich.tree.Tree(str(project_id))
    if old_backup_dir is None:
        tree.add(f"[i]Backup directory:[/] [b]{Formatted(new_backup_dir)}[/]")
    else:
        tree.add(
            f"[i]Backup directory:[/] [dim]{Formatted(old_backup_dir)}[/] => [b]{Formatted(new_backup_dir)}[/]")
    backup_node = tree.add('[i]Backup items[/]')

    # Schedule config.json
    config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
    backup_node.add(config_group)

    # Schedule compose.yaml
    backup_node.add(f"[green]{Formatted(COMPOSE_CONFIG_YAML)}[/]")

    # Schedule project files
    job = BackupJob(source_path='.', target_path='project-files',
                    project_dir=project.dir,
                    is_dir=True)
    if config.tasks.backup_project_dir:
        jobs.append(job)
        backup_node.add(str(format_do_backup(job)))
        config.tasks.backup_project_dir = [job.relative_source_path,
                                           job.relative_target_path]
    else:
        backup_node.add(str(format_no_backup(job, 'project dir')))

    has_running_or_restarting = False

    # Schedule volumes
    volumes_included: t.Set[str] = set()
    for service_name, service in project.config['services'].items():
        state = next((s['State'] for s in project.ps if s['Service'] == service_name), 'exited')
        if state in ['running', 'restarting']:
            has_running_or_restarting = True

        s = backup_node.add(f"[b]{Formatted(service_name)}[/] [i]{Formatted(state)}[/]")
        service_task = BackupConfigServiceTask(name=service_name)
        config.tasks.backup_services.append(service_task)

        volumes = service.get('volumes', [])
        for volume in volumes:
            job = BackupJob(source_path=volume['source'],
                            target_path=os.path.join('volumes', service_name, dir_from_path(volume['target'])),
                            project_dir=project.dir,
                            check_is_dir=True)

            if options.include_project_dir and (
                relative_path_if_below(job.rsync_source_path) + '/').startswith(project.dir + '/'):
                s.add(str(format_no_backup(job, 'already included', emphasize=False)))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue

            if job.rsync_source_path in volumes_included:
                s.add(str(format_no_backup(job, 'already included', emphasize=False)))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue

            is_bind_mount = volume['type'] == 'bind'
            if not is_bind_mount:
                s.add(str(format_no_backup(job, 'no bind mount')))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue
            ro = volume.get('read_only', False)
            if ro and not options.include_read_only_volumes:
                s.add(str(format_no_backup(job, 'read-only')))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue
            found = False
            for volume_regex in options.volumes:
                if re.search(volume_regex, job.rsync_source_path):
                    found = True
                    break
            if not found:
                s.add(str(format_no_backup(job, 'expressions don\'t match')))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue

            jobs.append(job)
            s.add(str(format_do_backup(job)))
            service_task.backup_volumes.append(
                (job.relative_source_path, job.relative_target_path))
            volumes_included.add(job.rsync_source_path)

        if len(volumes) == 0:
            s.add('[dim](no volumes)[/]')

    run_node = rich.tree.Tree('[i]Would run[/]')
    if options.dry_run_verbose:
        tree.add(run_node)

    config.tasks.restart_project = not options.live and has_running_or_restarting

    do_backup(project=project, options=options, config=config, jobs=jobs, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(config.json(indent=4)),
                                 expand=False,
                                 border_style='green')
            )

        rich.print(tree)


def add_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument('-e', '--exclude-project-dir', action='store_true', help='exclude project directory')
    parser.add_argument('-r', '--include-ro', action='store_true',
                        help='also consider read-only volumes')
    parser.add_argument('-v', '--volume', action='append',
                        default=[r'^(?!/(bin|boot|dev|etc|lib\w*|proc|run|sbin|sys|tmp|usr|var)/)'],
                        help='regex for volume selection, can be specified multiple times, '
                             'defaults to exclude many system directories, '
                             'use -v \'(?!)\' to exclude all volumes, '
                             'use -v ^/path/ to only allow specified paths')
    parser.add_argument('--live', action='store_true', help='do not stop the services before backup')
    parser.add_argument('--verbose', action='store_true', help='print more details if --dry-run')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually backup, only show what would be done')


def main(args) -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to do a backup.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    for project in get_compose_projects(args.projects, ProjectSearchOptions(
        print_compose_errors=args.dry_run,
        only_running=args.running,
    )):
        backup_project(
            project=project,
            options=BackupOptions(
                include_project_dir=not args.exclude_project_dir,
                include_read_only_volumes=args.include_ro,
                volumes=args.volume,
                live=args.live,
                dry_run=args.dry_run,
                dry_run_verbose=args.verbose,
            )
        )

    return 0
