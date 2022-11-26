import re
import shlex
import subprocess
import typing as t

import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree
import typer

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
    special_characters = "~`#$&*()|[]{};'\"<>?!@:="
    # special_characters, for our purposes, inludes the characters listed here
    # https://www.oreilly.com/library/view/learning-the-bash/1565923472/ch01s09.html
    # plus '@:=' (we want to highlight that)
    # minus '/\\' ('/' will be formatted with paths, '\\' could be an escape character for rich).

    highlight_path_segments = False

    cmdline = str(Formatted(shlex.join(cmd)))
    cmdline = re.sub(f"([{re.escape(special_characters)}])", r"[/][dark_orange]\1[/][dim]", cmdline)
    cmdline = re.sub(r"(?<![-\w])(--?\w[-\w]*)", r"[/][dim dark_orange]\1[/][dim]", cmdline)
    cmdline = re.sub(
        r"(?=^|(?<=[ \]]))(/" + f"[^{re.escape(special_characters)}/\\ ]+" + r")",
        r"[/][yellow]\1[/][dim]",
        cmdline,
    )
    if highlight_path_segments:
        cmdline = re.sub(r"(?<!\[yellow\])(/)(?!\])", r"[/][yellow]\1[/][dim]", cmdline)
    cmdline = re.sub(r" -- ", r"[/] [dark_orange]--[/] [dim]", cmdline)
    cmdline = f"[dim]{cmdline}[/]"

    if len(cmd) > 0:
        program = str(Formatted(cmd[0]))
        if cmdline.startswith(f"[dim]{program} "):
            cmdline = f"[dark_orange]{program}[/][dim]" + cmdline[5 + len(program) :]
    return Formatted(cmdline, True)


def rich_print_cmd(cmd: list[str], cwd: t.Optional[str]) -> None:
    rich.print(
        rich.panel.Panel(
            str(format_cmd_line(cmd)),
            title=f"[i]Running in[/] [yellow]{relative_path_if_below(cwd)}[/]" if cwd else "[i]Running[/]",
            title_align="left",
        )
    )


class RichAbortCmd(typer.Exit):
    def __init__(self, error: subprocess.CalledProcessError):
        stderr = error.stderr.strip() if error.stderr is not None else ""
        rich.print(
            rich.panel.Panel(
                f"$ {format_cmd_line(error.cmd)}\n" f"[red dim]{Formatted(stderr, already_formatted=True)}[/]"
                if stderr != ""
                else str(format_cmd_line(error.cmd)),
                title=f"[red]Exit code [b]{error.returncode}[/][/]",
                title_align="left",
            )
        )
        super().__init__(error.returncode)
