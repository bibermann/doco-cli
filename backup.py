#!/usr/bin/env python3
import argparse
import dataclasses
import datetime
import os
import re
import sys
import tempfile
import typing as t

import pydantic
import rich
import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from utils.common import relative_path_if_below
from utils.rich import ComposeProject
from utils.rich import format_cmd_line
from utils.rich import Formatted
from utils.rich import get_compose_projects
from utils.rich import ProjectSearchOptions
from utils.rich import rich_run_compose
from utils.rsync import run_rsync_backup_with_hardlinks
from utils.rsync import run_rsync_without_delete

LAST_BACKUP_DIR_FILENAME = '.last-backup-dir'


@dataclasses.dataclass
class BackupOptions:
    include_project_dir: bool
    include_read_only_volumes: bool
    volumes: t.List[str]
    dry_run: bool
    dry_run_verbose: bool


@dataclasses.dataclass
class BackupJob:
    relative_source_path: str
    relative_target_path: str
    rsync_source_path: str
    rsync_target_path: str
    is_dir: bool

    def __init__(self, source_path: str, target_path: str,
                 is_dir: t.Optional[bool] = None, check_is_dir: bool = False):
        if is_dir is not None:
            if check_is_dir:
                raise ValueError('check_is_dir cannot be True if is_dir is not None.')
            self.is_dir = is_dir
        else:
            if check_is_dir:
                self.is_dir = os.path.isdir(source_path)
            else:
                self.is_dir = source_path.endswith('/')
        self.relative_source_path = relative_path_if_below(source_path) + ('/' if is_dir else '')
        self.relative_target_path = relative_path_if_below(target_path) + ('/' if is_dir else '')
        self.rsync_source_path = os.path.abspath(source_path) + ('/' if is_dir else '')
        self.rsync_target_path = os.path.normpath(target_path)


def format_do_backup(job: BackupJob) -> Formatted:
    return Formatted(
        f"[green][b]{Formatted(job.relative_source_path)}[/] [dim]as[/] {Formatted(job.relative_target_path)}[/]",
        True)


def format_no_backup(job: BackupJob, reason: str, emphasize: bool = True) -> Formatted:
    if emphasize:
        return Formatted(f"[red]{Formatted(job.relative_source_path)} [dim]({Formatted(reason)})[/][/]", True)
    else:
        return Formatted(f"{Formatted(job.relative_source_path)} [dim]({Formatted(reason)})[/]", True)


def dir_from_path(path: str) -> str:
    if path.startswith('/'):
        path = path[1:]
    result = path.replace('/', '__')
    return result


def load_last_backup_directory(project_dir: str) -> t.Optional[str]:
    path = os.path.join(project_dir, LAST_BACKUP_DIR_FILENAME)
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as f:
            value = f.readline().strip()
            if value != '' and not '..' in value and not value.startswith('/'):
                return value


def save_last_backup_directory(project_dir: str, value: str) -> None:
    path = os.path.join(project_dir, LAST_BACKUP_DIR_FILENAME)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(value)


class BackupConfigServiceTask(pydantic.BaseModel):
    name: str
    backup_volumes: t.List[t.Tuple[str, str]] = []
    exclude_volumes: t.List[str] = []


class BackupConfigOptions(pydantic.BaseModel):
    include_project_dir: bool
    include_read_only_volumes: bool
    volume_patterns: t.List[str]


class BackupConfigTasks(pydantic.BaseModel):
    restart_project: bool = False
    create_last_backup_dir_file: bool
    backup_config: bool
    backup_compose_file: bool
    backup_project_dir: bool
    backup_services: t.List[BackupConfigServiceTask] = []


class BackupConfig(pydantic.BaseModel):
    project_path: str
    compose_file: str
    timestamp: datetime.datetime
    backup_dir: str
    last_backup_dir: t.Optional[str]
    options: BackupConfigOptions
    tasks: BackupConfigTasks


def do_backup_config(new_backup_dir: str, old_backup_dir: t.Optional[str], config: BackupConfig,
                     target_file_name: str, dry_run: bool, rich_node: rich.tree.Tree):
    with tempfile.TemporaryDirectory() as tmp_dir:
        source = os.path.join(tmp_dir, target_file_name)
        with open(source, 'w', encoding='utf-8') as f:
            f.write(config.json(indent=4))
        cmd = run_rsync_backup_with_hardlinks(
            source=source,
            destination_root='services', new_backup=os.path.join(new_backup_dir, target_file_name),
            old_backup_dirs=[old_backup_dir] if old_backup_dir is not None else [],
            dry_run=dry_run
        )
        rich_node.add(str(format_cmd_line(cmd)))


def do_backup_job(new_backup_dir: str, old_backup_dir: t.Optional[str],
                  job: BackupJob, dry_run: bool,
                  rich_node: rich.tree.Tree):
    if old_backup_dir is not None:
        old_backup_path = os.path.normpath(os.path.join(old_backup_dir, job.rsync_target_path))
        if not job.is_dir:
            old_backup_path = os.path.dirname(old_backup_path)
    else:
        old_backup_path = None
    cmd = run_rsync_backup_with_hardlinks(
        source=job.rsync_source_path,
        destination_root='services',
        new_backup=os.path.join(new_backup_dir, job.rsync_target_path),
        old_backup_dirs=[old_backup_path] if old_backup_path is not None else [],
        dry_run=dry_run
    )
    rich_node.add(str(format_cmd_line(cmd)))


def create_target_structure(new_backup_dir: str, jobs: t.Iterable[BackupJob], dry_run: bool,
                            rich_node: rich.tree.Tree):
    """Create target directory structure at destination

    Required as long as remote rsync does not implement --mkpath
    """

    paths = set(
        os.path.dirname(os.path.normpath(os.path.join(new_backup_dir, job.rsync_target_path)))
        for job in jobs
    )
    leafs = [leaf for leaf in paths if
             leaf != '' and next((path for path in paths if path.startswith(f"{leaf}/")), None) is None]

    with tempfile.TemporaryDirectory() as tmp_dir:
        for leaf in leafs:
            os.makedirs(os.path.join(tmp_dir, leaf))
        cmd = run_rsync_without_delete(
            source=f"{tmp_dir}/",
            destination_root='services', destination='',
            dry_run=dry_run
        )
        rich_node.add(str(format_cmd_line(cmd)))


def do_backup(project: ComposeProject, options: BackupOptions, config: BackupConfig, jobs: t.List[BackupJob],
              run_node: rich.tree.Tree):
    create_target_structure(config.backup_dir, jobs, dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.restart_project:
        rich_run_compose(project.dir, project.file,
                         command=['down'],
                         dry_run=options.dry_run, rich_node=run_node)

    # Backup scheduled files
    if config.tasks.backup_config:
        do_backup_config(config.backup_dir, config.last_backup_dir, config, 'config.json',
                         dry_run=options.dry_run,
                         rich_node=run_node)

    for job in jobs:
        do_backup_job(config.backup_dir, config.last_backup_dir, job, dry_run=options.dry_run,
                      rich_node=run_node)

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
        options=BackupConfigOptions(
            include_project_dir=options.include_project_dir,
            include_read_only_volumes=options.include_read_only_volumes,
            volume_patterns=options.volumes,
        ),
        tasks=BackupConfigTasks(
            create_last_backup_dir_file=True,
            backup_config=True,
            backup_compose_file=not options.include_project_dir,
            backup_project_dir=options.include_project_dir,
        ),
    )
    jobs: t.List[BackupJob] = []

    tree = rich.tree.Tree(str(project_id))
    if old_backup_dir is None:
        tree.add(f"[i]Backup directory:[/] [b]{Formatted(new_backup_dir)}[/]")
    else:
        tree.add(
            f"[i]Backup directory:[/] [dim]{Formatted(old_backup_dir)}[/] => [b]{Formatted(new_backup_dir)}[/]")
    backup_node = tree.add('[i]Backup items[/]')

    # Schedule config.json
    config_group = rich.console.Group('[green]config.json[/]')
    backup_node.add(config_group)

    # Schedule compose.yaml
    job = BackupJob(source_path=os.path.join(project.dir, project.file), target_path='compose.yaml',
                    is_dir=False)
    if config.tasks.backup_compose_file:
        jobs.append(job)
        backup_node.add(str(format_do_backup(job)))
    else:
        backup_node.add(str(format_no_backup(job, 'already included', emphasize=False)))

    # Schedule project files
    job = BackupJob(source_path=project.dir, target_path='project-files', is_dir=True)
    if config.tasks.backup_project_dir:
        jobs.append(job)
        backup_node.add(str(format_do_backup(job)))
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
                            is_dir=os.path.isdir(volume['source']))

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
            service_task.backup_volumes.append((job.rsync_source_path, job.rsync_target_path))
            volumes_included.add(job.rsync_source_path)

        if len(volumes) == 0:
            s.add('[dim](no volumes)[/]')

    run_node = rich.tree.Tree('[i]Would run[/]')
    if options.dry_run_verbose:
        tree.add(run_node)

    config.tasks.restart_project = has_running_or_restarting

    do_backup(project=project, options=options, config=config, jobs=jobs, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(config.json(indent=4)),
                                 expand=False,
                                 border_style='green')
            )

        rich.print(tree)


def main() -> int:
    if not (os.geteuid() == 0):
        exit("You need to have root privileges to run this script.\n"
             "Please try again, this time using 'sudo'. Exiting.")

    parser = argparse.ArgumentParser()
    parser.add_argument('projects', nargs='*', default=['.'],
                        help='compose files and/or directories containing a docker-compose.y[a]ml')
    parser.add_argument('--running', action='store_true',
                        help='consider only projects with at least one running or restarting service')
    parser.add_argument('-d', '--include-project-dir', action='store_true', help='include project directory')
    parser.add_argument('-r', '--include-ro', action='store_true',
                        help='also consider read-only volumes')
    parser.add_argument('-v', '--volume', action='append', default=[], help='regex for volume selection')
    parser.add_argument('--verbose', action='store_true', help='print more details if --dry-run')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually backup, only show what would be done')
    args = parser.parse_args()

    for project in get_compose_projects(args.projects, ProjectSearchOptions(only_running=args.running)):
        backup_project(
            project=project,
            options=BackupOptions(
                include_project_dir=args.include_project_dir,
                include_read_only_volumes=args.include_ro,
                volumes=args.volume,
                dry_run=args.dry_run,
                dry_run_verbose=args.verbose,
            )
        )

    return 0


if __name__ == '__main__':
    sys.exit(main())
