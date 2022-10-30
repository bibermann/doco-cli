import os
import pathlib
import typing as t

import typer.core

from . import create as cmd_create
from . import download as cmd_download
from . import list as cmd_list
from . import restore as cmd_restore
from src.utils.bbak import BbakContextObject
from src.utils.completers import DirectoryCompleter
from src.utils.doco_config import load_doco_config


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, _):
        return self.commands.keys()


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name="ls")(cmd_list.main)
app.command(name="download")(cmd_download.main)
app.command(name="create")(cmd_create.main)
app.command(name="restore")(cmd_restore.main)


@app.callback()
def main(
    ctx: typer.Context,
    workdir: pathlib.Path = typer.Option(
        ".",
        "--workdir",
        "-w",
        shell_complete=DirectoryCompleter().__call__,
        file_okay=False,
        exists=True,
        help="Change working directory.",
    ),
    root: t.Optional[str] = typer.Option(None, "--root", "-r", help="Change root."),
):
    """
    Manage backups (independently of [i]docker compose[/]).
    """

    doco_config = load_doco_config(str(workdir))
    if root is not None:
        doco_config.backup.rsync.root = os.path.normpath(os.path.join(doco_config.backup.rsync.root, root))

    ctx.obj = BbakContextObject(workdir=str(workdir), doco_config=doco_config)
