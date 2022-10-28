#!/usr/bin/env python3

import os
import pathlib
import typing as t

import typer.core

import bbak_cmd.backup
import bbak_cmd.get_backup
import bbak_cmd.list
import bbak_cmd.restore
from utils.bbak import BbakContextObject
from utils.completers import DirectoryCompleter
from utils.doco_config import load_doco_config
from utils.validators import project_id_callback


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, ctx):
        return self.commands.keys()


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name='ls')(bbak_cmd.list.main)
app.command(name='backup')(bbak_cmd.backup.main)
app.command(name='get')(bbak_cmd.get_backup.main)
app.command(name='restore')(bbak_cmd.restore.main)


@app.callback()
def main(
    ctx: typer.Context,
    workdir: pathlib.Path = typer.Option('.', '--workdir', '-w',
                                         autocompletion=DirectoryCompleter().__call__, file_okay=False,
                                         exists=True,
                                         help='Change working directory.'),
    root: t.Optional[str] = typer.Option(None, '--root', '-r',
                                         help='Change root.'),
    project_id: t.Optional[str] = typer.Option(None, '--project', '-p',
                                               callback=project_id_callback,
                                               help='Target project to retrieve backups from.'),
):
    """
    [b]bbak[/] ([b]b[/]iber [b]ba[/]c[b]k[/]up tool) is a command line tool for listing and downloading (not restoring) backups created by [i]doco[/].
    It is also able to back up and restore files and directories that are not part of a [i]docker compose[/] project.
    """

    doco_config = load_doco_config(str(workdir))
    if root is not None:
        doco_config.backup.rsync.root = \
            os.path.normpath(os.path.join(doco_config.backup.rsync.root, root))

    ctx.obj = BbakContextObject(workdir=str(workdir), project_id=project_id, doco_config=doco_config)


if __name__ == "__main__":
    app()
