#!/usr/bin/env python3
import argparse
import dataclasses
import datetime
import os
import re
import subprocess
import sys
import tempfile
import typing as t

import pydantic
import rich
import rich.console
import rich.json
import rich.panel
import rich.pretty
import rich.tree

from common import find_compose_projects
from common import load_compose_config
from common import load_compose_ps
from common import relative_path_if_below
from common import run_rsync_backup_with_hardlinks
from common import run_rsync_without_delete


@dataclasses.dataclass
class BackupOptions:
    include_project_dir: bool
    include_read_only_volumes: bool
    volumes: t.List[str]
    dry_run: bool
    dry_run_verbose: bool


def format_do_backup(path: str, target: str, emphasize: bool = True) -> str:
    if emphasize:
        return f"[green][b]{path}[/] [dim]as[/] {target}[/]"
    else:
        return f"[green]{path} [dim]as[/] {target}[/]"


def format_no_backup(path: str, reason: str, emphasize: bool = True) -> str:
    if emphasize:
        return f"[red]{path} [dim]({reason})[/][/]"
    else:
        return f"{path} [dim]({reason})[/]"


def format_cmd_line(cmd: t.List[str])-> rich.console.RenderableType:
    return '\[' + ', '.join(f"[dim]{item}[/]" for item in cmd) + ']'


def dir_from_path(path: str) -> str:
    if path[0:1] == '/':
        path = path[1:]
    result = path.replace('/', '__')
    return result


class BackupServiceConfig(pydantic.BaseModel):
    name: str
    included_volumes: t.List[t.Tuple[str, str]] = []
    excluded_volumes: t.List[str] = []


class BackupConfig(pydantic.BaseModel):
    project_path: str
    timestamp: datetime.datetime
    include_project_dir: bool
    include_read_only_volumes: bool
    volume_patterns: t.List[str]
    services: t.List[BackupServiceConfig] = []


def do_backup_config(new_backup_dir: str, old_backup_dir: t.Optional[str], config: BackupConfig,
                     target_file_name: str, dry_run: bool, rich_node: rich.tree.Tree):
    with tempfile.TemporaryDirectory() as tmp_dir:
        source = os.path.join(tmp_dir, target_file_name)
        with open(source, 'w') as f:
            f.write(config.json(indent=4))
        cmd = run_rsync_backup_with_hardlinks(
            source=source,
            destination_root='services', new_backup=os.path.join(new_backup_dir, target_file_name),
            old_backup_dirs=[old_backup_dir] if old_backup_dir is not None else [],
            dry_run=dry_run
        )
        rich_node.add(format_cmd_line(cmd))


@dataclasses.dataclass
class BackupJob:
    source_path: str
    target_path: str


def do_backup_job(new_backup_dir: str, old_backup_dir: t.Optional[str], job: BackupJob, dry_run: bool,
                  rich_node: rich.tree.Tree):
    cmd = run_rsync_backup_with_hardlinks(
        source=job.source_path,
        destination_root='services',
        new_backup=os.path.join(new_backup_dir, job.target_path),
        old_backup_dirs=[old_backup_dir] if old_backup_dir is not None else [],
        dry_run=dry_run
    )
    rich_node.add(format_cmd_line(cmd))


def create_target_structure(new_backup_dir: str, jobs: t.Iterable[BackupJob], dry_run: bool,
                            rich_node: rich.tree.Tree):
    """Create target directory structure at destination

    Required as long as remote rsync does not implement --mkpath
    """

    def get_parent_dir(path: str):
        if path.endswith('/'):
            path = path[:-1]
        return os.path.dirname(path)

    paths = set(get_parent_dir(os.path.join(new_backup_dir, job.target_path)) for job in jobs)
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
        rich_node.add(format_cmd_line(cmd))


def backup_project(compose_dir: str, compose_file: str, options: BackupOptions):
    try:
        compose_config = load_compose_config(compose_dir, compose_file)
    except subprocess.CalledProcessError as e:
        tree = rich.tree.Tree(f"[b]{os.path.join(compose_dir, compose_file)}")
        tree.add(f'[red]{e.stderr.strip()}')
        rich.print(tree)
        return

    compose_ps = load_compose_ps(compose_dir, compose_file)

    compose_name = compose_config['name']
    compose_id = f"[b]{compose_name}[/]"
    compose_id += f" [dim]{os.path.join(compose_dir, compose_file)}[/]"

    now = datetime.datetime.now()
    today_iso = now.date().isoformat()
    yesterday_iso = (now.date() - datetime.timedelta(days=1)).isoformat()
    new_backup_dir = os.path.join(compose_name, f"backup-{today_iso}")
    old_backup_dir = os.path.join(compose_name, f"backup-{yesterday_iso}")

    config = BackupConfig(
        project_path=os.path.abspath(compose_dir),
        timestamp=now,
        include_project_dir=options.include_project_dir,
        include_read_only_volumes=options.include_read_only_volumes,
        volume_patterns=options.volumes,
    )
    jobs: t.List[BackupJob] = []

    tree = rich.tree.Tree(compose_id)
    tree.add(f"[i]Project directory:[/] [b]{new_backup_dir}[/]")
    backup_node = tree.add('[i]Backups[/]')

    # Schedule config.json
    config_group = rich.console.Group('[green]config.json[/]')
    backup_node.add(config_group)

    # Schedule compose.yaml
    source_path = os.path.join(compose_dir, compose_file)
    target_path = 'compose.yaml'
    backup_node.add(format_do_backup(source_path, target_path))
    jobs.append(BackupJob(source_path=source_path, target_path=target_path))

    # Schedule project files
    if options.include_project_dir:
        target_path = 'project-files/'
        backup_node.add(format_do_backup(compose_dir, target_path))
        jobs.append(BackupJob(source_path=compose_dir, target_path=target_path))
    else:
        backup_node.add(format_no_backup(compose_dir, 'project dir'))

    # Schedule volumes
    volumes_included: t.Set[str] = set()
    for service_name, service in compose_config['services'].items():
        state = next((s['State'] for s in compose_ps if s['Service'] == service_name), 'exited')

        s = backup_node.add(f"service [b]{service_name}[/] [dim]{state}[/]")
        s_config = BackupServiceConfig(name=service_name)
        config.services.append(s_config)

        volumes = service.get('volumes', [])
        for volume in volumes:
            source = volume['source']
            target = volume['target']

            if options.include_project_dir and relative_path_if_below(source).startswith(compose_dir):
                s.add(format_no_backup(source, 'already included', emphasize=False))
                s_config.excluded_volumes.append(source)
                continue

            if source in volumes_included:
                s.add(format_no_backup(source, 'already included', emphasize=False))
                s_config.excluded_volumes.append(source)
                continue

            is_bind_mount = volume['type'] == 'bind'
            if not is_bind_mount:
                s.add(format_no_backup(source, 'no bind mount'))
                s_config.excluded_volumes.append(source)
                continue
            ro = volume.get('read_only', False)
            if ro and not options.include_read_only_volumes:
                s.add(format_no_backup(source, 'read-only'))
                s_config.excluded_volumes.append(source)
                continue
            found = False
            for volume_regex in options.volumes:
                if re.search(volume_regex, source):
                    found = True
                    break
            if not found:
                s.add(format_no_backup(source, 'expressions don\'t match'))
                s_config.excluded_volumes.append(source)
                continue

            target_path = os.path.join('volumes', service_name, dir_from_path(target))
            s.add(format_do_backup(source, target_path))
            s_config.included_volumes.append((source, target_path))
            jobs.append(BackupJob(source_path=source, target_path=target_path))
            volumes_included.add(source)

        if len(volumes) == 0:
            s.add('no volumes')

    run_node = rich.tree.Tree('Would run')
    if options.dry_run_verbose:
        tree.add(run_node)

    create_target_structure(new_backup_dir, jobs, dry_run=options.dry_run, rich_node=run_node)

    # Backup scheduled files
    do_backup_config(new_backup_dir, old_backup_dir, config, 'config.json', dry_run=options.dry_run,
                     rich_node=run_node)
    for job in jobs:
        do_backup_job(new_backup_dir, old_backup_dir, job, dry_run=options.dry_run, rich_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(config.json(indent=4)),
                                                       expand=False,
                                                       border_style='green')
            )

        rich.print(tree)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('projects', nargs='*', default=['.'],
                        help='compose files and/or directories containing a docker-compose.y[a]ml')
    parser.add_argument('-d', '--include-project-dir', action='store_true', help='include project directory')
    parser.add_argument('-r', '--include-ro', action='store_true',
                        help='also consider read-only volumes')
    parser.add_argument('-v', '--volume', nargs='+', default=[], help='regex for volume selection')
    parser.add_argument('--verbose', action='store_true',help='print more details if --dry-run')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='do not actually backup, only show what would be done')
    args = parser.parse_args()

    for compose_dir, compose_file in find_compose_projects(args.projects):
        backup_project(
            compose_dir=compose_dir,
            compose_file=compose_file,
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
