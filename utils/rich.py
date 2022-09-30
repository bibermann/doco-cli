import os
import re
import shlex
import typing as t

import rich
import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from .common import run_compose


def format_cmd_line(cmd: t.List[str]) -> rich.console.RenderableType:
    cmdline = rich.markup.escape(shlex.join(cmd))
    cmdline = re.sub(r' (--?[^ =-][^ =]*)', r' [/][dim dark_orange]\1[/][dim]', cmdline)
    cmdline = re.sub(r'([\'"\\])', r'[/][dark_orange]\1[/][dim]', cmdline)
    cmdline = re.sub(r' -- ', r'[/] [dark_orange]--[/] [dim]', cmdline)
    cmdline = f"[dim]{cmdline}[/]"
    if len(cmd) > 0:
        program = rich.markup.escape(cmd[0])
        if cmdline.startswith(f"[dim]{program} "):
            cmdline = f"[dark_orange]{program}[/][dim]" + cmdline[5 + len(program):]
    return cmdline


def rich_run_compose(compose_dir, compose_file, command: t.List[str], dry_run: bool,
                     rich_node: rich.tree.Tree, cancelable: bool = False):
    cmd = run_compose(
        compose_dir=os.path.abspath(compose_dir),
        compose_file=compose_file,
        command=command,
        dry_run=dry_run,
        cancelable=cancelable,
    )
    rich_node.add(format_cmd_line(cmd))
