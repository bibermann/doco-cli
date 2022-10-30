import re
import shlex
import typing as t

import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from src.utils.common import relative_path_if_below


class Formatted:
    def __init__(self, text: t.Union[str, "Formatted"], already_formatted: bool = False):
        if already_formatted or isinstance(text, Formatted):
            self._text = str(text)
        else:
            self._text = rich.markup.escape(text)

    def __str__(self):
        return self._text


def format_cmd_line(cmd: list[str]) -> Formatted:
    cmdline = str(Formatted(shlex.join(cmd)))
    cmdline = re.sub(r" (--?[^ =-][^ =]*)", r" [/][dim dark_orange]\1[/][dim]", cmdline)
    cmdline = re.sub(r'([\'"@:])', r"[/][dark_orange]\1[/][dim]", cmdline)
    cmdline = re.sub(r'((?<=[ \'":])/[^/]*)', r"[/][yellow]\1[/][dim]", cmdline)
    cmdline = re.sub(r" -- ", r"[/] [dark_orange]--[/] [dim]", cmdline)
    cmdline = f"[dim]{cmdline}[/]"
    if len(cmd) > 0:
        program = str(Formatted(cmd[0]))
        if cmdline.startswith(f"[dim]{program} "):
            cmdline = f"[dark_orange]{program}[/][dim]" + cmdline[5 + len(program) :]
    return Formatted(cmdline, True)


def rich_print_cmd(cmd: list[str], cwd: t.Optional[str]) -> None:
    if cwd:
        rich.print(
            rich.tree.Tree(
                f"[i]Running[/] {format_cmd_line(cmd)} [i]in[/] [yellow]{relative_path_if_below(cwd)}[/]"
            )
        )
    else:
        rich.print(rich.tree.Tree(f"[i]Running[/] {format_cmd_line(cmd)}"))
