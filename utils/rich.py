import dataclasses
import os
import re
import shlex
import subprocess
import typing as t

import rich
import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from .compose import find_compose_projects
from .compose import load_compose_config
from .compose import load_compose_ps
from .compose import run_compose


class Formatted:
    def __init__(self, text: t.Union[str, 'Formatted'], already_formatted: bool = False):
        if already_formatted or isinstance(text, Formatted):
            self._text = str(text)
        else:
            self._text = rich.markup.escape(text)

    def __str__(self):
        return self._text


@dataclasses.dataclass
class ProjectSearchOptions:
    only_running: bool


@dataclasses.dataclass
class ComposeProject:
    dir: str
    file: str
    config: any
    ps: any


def format_cmd_line(cmd: t.List[str]) -> Formatted:
    cmdline = str(Formatted(shlex.join(cmd)))
    cmdline = re.sub(r' (--?[^ =-][^ =]*)', r' [/][dim dark_orange]\1[/][dim]', cmdline)
    cmdline = re.sub(r'([\'"@:])', r'[/][dark_orange]\1[/][dim]', cmdline)
    cmdline = re.sub(r'((?<=[ \'":])/[^/]*)', r'[/][yellow]\1[/][dim]', cmdline)
    cmdline = re.sub(r' -- ', r'[/] [dark_orange]--[/] [dim]', cmdline)
    cmdline = f"[dim]{cmdline}[/]"
    if len(cmd) > 0:
        program = str(Formatted(cmd[0]))
        if cmdline.startswith(f"[dim]{program} "):
            cmdline = f"[dark_orange]{program}[/][dim]" + cmdline[5 + len(program):]
    return Formatted(cmdline, True)


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


def get_compose_projects(paths: t.Iterable[str], options: ProjectSearchOptions) -> t.Generator[
    ComposeProject, None, None]:
    for project_dir, project_file in find_compose_projects(paths):
        try:
            project_config = load_compose_config(project_dir, project_file)
        except subprocess.CalledProcessError as e:
            tree = rich.tree.Tree(f"[b]{Formatted(os.path.join(project_dir, project_file))}")
            tree.add(f'[red]{Formatted(e.stderr.strip())}')
            rich.print(tree)
            return

        project_ps = load_compose_ps(project_dir, project_file)

        project = ComposeProject(
            dir=project_dir,
            file=project_file,
            config=project_config,
            ps=project_ps,
        )

        if options.only_running:
            has_running_or_restarting = False
            for service_name in project.config['services'].keys():
                state = next((s['State'] for s in project.ps if s['Service'] == service_name), 'exited')

                if state in ['running', 'restarting']:
                    has_running_or_restarting = True
                    break

            if not has_running_or_restarting:
                continue

        yield project
