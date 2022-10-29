#!/usr/bin/env python3

import typer.core

from commands import backups as cmd_backups
from commands import down as cmd_down
from commands import log as cmd_log
from commands import restart as cmd_restart
from commands import status as cmd_status
from commands import up as cmd_up


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, ctx):
        return self.commands.keys()


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name='s')(cmd_status.main)
app.command(name='r')(cmd_restart.main)
app.command(name='d')(cmd_down.main)
app.command(name='u')(cmd_up.main)
app.command(name='l')(cmd_log.main)
app.add_typer(cmd_backups.app, name="backups")


@app.callback()
def main():
    """
    [b]doco[/] ([b]do[/]cker [b]co[/]mpose tool) is a command line tool for working with [i]docker compose[/] projects
    (pretty-printing status, creating backups using rsync, batch commands and more).
    """


if __name__ == "__main__":
    app()
