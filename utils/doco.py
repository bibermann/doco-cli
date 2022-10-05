import dataclasses
import os
import subprocess
import typing as t

import rich
import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from .common import load_compose_config
from .common import load_compose_ps
from .rich import Formatted


@dataclasses.dataclass
class ProjectInfo:
    has_running_or_restarting: bool
    all_running: bool
    run_node: rich.tree.Tree


def do_project_cmd(compose_dir: str, compose_file: str, dry_run: bool,
                   cmd_task: t.Callable[[ProjectInfo], None]):
    try:
        compose_config = load_compose_config(compose_dir, compose_file)
    except subprocess.CalledProcessError as e:
        tree = rich.tree.Tree(f"[b]{Formatted(os.path.join(compose_dir, compose_file))}")
        tree.add(f'[red]{Formatted(e.stderr.strip())}')
        rich.print(tree)
        return

    compose_ps = load_compose_ps(compose_dir, compose_file)

    compose_name = compose_config['name']
    compose_id = f"[b]{Formatted(compose_name)}[/]"
    compose_id += f" [dim]{Formatted(os.path.join(compose_dir, compose_file))}[/]"

    tree = rich.tree.Tree(compose_id)

    has_running_or_restarting = False
    all_running = True

    for service_name, service in compose_config['services'].items():
        state = next((s['State'] for s in compose_ps if s['Service'] == service_name), 'exited')

        if state in ['running', 'restarting']:
            has_running_or_restarting = True

        if state != 'running':
            all_running = False

        tree.add(f"[b]{Formatted(service_name)}[/] [i]{Formatted(state)}[/]")

    run_node = rich.tree.Tree('[i]Would run[/]')
    if dry_run:
        tree.add(run_node)

    cmd_task(ProjectInfo(
        has_running_or_restarting=has_running_or_restarting,
        all_running=all_running,
        run_node=run_node,
    ))

    if len(run_node.children) == 0:
        run_node.add('[dim](nothing)[/]')

    if dry_run:
        rich.print(tree)
