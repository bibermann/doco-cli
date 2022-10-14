import dataclasses
import os
import subprocess
import typing as t

import rich
import rich.tree

from utils.compose import find_compose_projects
from utils.compose import load_compose_config
from utils.compose import load_compose_ps
from utils.compose import run_compose
from utils.doco_config import DocoConfig
from utils.doco_config import load_doco_config
from utils.rich import format_cmd_line
from utils.rich import Formatted


@dataclasses.dataclass
class ComposeProject:
    dir: str
    file: str
    config: t.Mapping[str, any]
    config_yaml: str
    ps: t.Mapping[str, any]
    doco_config: DocoConfig


@dataclasses.dataclass
class ProjectSearchOptions:
    print_compose_errors: bool
    only_running: bool
    allow_empty: bool = False


def get_compose_projects(paths: t.Iterable[str], options: ProjectSearchOptions) \
    -> t.Generator[ComposeProject, None, None]:
    for project_dir, project_file in find_compose_projects(paths, options.allow_empty):
        if not (options.allow_empty and project_file == ''):
            try:
                project_config, project_config_yaml = load_compose_config(project_dir, project_file)
            except subprocess.CalledProcessError as e:
                if options.print_compose_errors:
                    tree = rich.tree.Tree(f"[b]{Formatted(os.path.join(project_dir, project_file))}")
                    tree.add(f'[red]{Formatted(e.stderr.strip())}')
                    rich.print(tree)
                continue

            project_ps = load_compose_ps(project_dir, project_file)

            if options.only_running:
                has_running_or_restarting = False
                for service_name in project_config['services'].keys():
                    state = next((s['State'] for s in project_ps if s['Service'] == service_name), 'exited')

                    if state in ['running', 'restarting']:
                        has_running_or_restarting = True
                        break

                if not has_running_or_restarting:
                    continue
        else:
            project_config = {}
            project_config_yaml = str
            project_ps = {}

        yield ComposeProject(
            dir=project_dir,
            file=project_file,
            config=project_config,
            config_yaml=project_config_yaml,
            ps=project_ps,
            doco_config=load_doco_config(project_dir)
        )


def rich_run_compose(project_dir, project_file, command: t.List[str], dry_run: bool,
                     rich_node: rich.tree.Tree, cancelable: bool = False):
    cmd = run_compose(
        project_dir=os.path.abspath(project_dir),
        project_file=project_file,
        command=command,
        dry_run=dry_run,
        cancelable=cancelable,
    )
    rich_node.add(str(format_cmd_line(cmd)))
