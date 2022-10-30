#!/usr/bin/env python3
import typing as t

import typer.core

from src.commands import backups as cmd_backups
from src.commands import down as cmd_down
from src.commands import log as cmd_log
from src.commands import restart as cmd_restart
from src.commands import status as cmd_status
from src.commands import up as cmd_up

__version__ = "0.1.3"


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, _):
        return self.commands.keys()


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name="s")(cmd_status.main)
app.command(name="r")(cmd_restart.main)
app.command(name="d")(cmd_down.main)
app.command(name="u")(cmd_up.main)
app.command(name="l")(cmd_log.main)
app.add_typer(cmd_backups.app, name="backups")


def version_callback(value: bool):
    if value:
        print(f"Doco CLI Version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _: t.Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version information and exit."
    ),
):
    """
    [b]doco[/] ([b]do[/]cker [b]co[/]mpose tool) is a command line tool
    for working with [i]docker compose[/] projects
    (pretty-printing status, creating backups using rsync, batch commands and more).
    """


if __name__ == "__main__":
    app()
