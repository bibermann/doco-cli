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

from .compose import run_compose


class Formatted:
    def __init__(self, text: t.Union[str, 'Formatted'], already_formatted: bool = False):
        if already_formatted or isinstance(text, Formatted):
            self._text = str(text)
        else:
            self._text = rich.markup.escape(text)

    def __str__(self):
        return self._text


def format_cmd_line(cmd: t.List[str]) -> Formatted:
    cmdline = rich.markup.escape(shlex.join(cmd))
    cmdline = re.sub(r' (--?[^ =-][^ =]*)', r' [/][dim dark_orange]\1[/][dim]', cmdline)
    cmdline = re.sub(r'([\'"\\])', r'[/][dark_orange]\1[/][dim]', cmdline)
    cmdline = re.sub(r' -- ', r'[/] [dark_orange]--[/] [dim]', cmdline)
    cmdline = f"[dim]{cmdline}[/]"
    if len(cmd) > 0:
        program = rich.markup.escape(cmd[0])
        if cmdline.startswith(f"[dim]{program} "):
            cmdline = f"[dark_orange]{program}[/][dim]" + cmdline[5 + len(program):]
    return Formatted(cmdline, True)


def rich_run_compose(compose_dir, compose_file, command: t.List[str], dry_run: bool,
                     rich_node: rich.tree.Tree, cancelable: bool = False):
    cmd = run_compose(
        compose_dir=os.path.abspath(compose_dir),
        compose_file=compose_file,
        command=command,
        dry_run=dry_run,
        cancelable=cancelable,
    )
    rich_node.add(str(format_cmd_line(cmd)))
