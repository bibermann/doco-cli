#!/usr/bin/env python3

import typer.core

import doco_cmd.backup
import doco_cmd.down
import doco_cmd.log
import doco_cmd.restart
import doco_cmd.restore
import doco_cmd.status
import doco_cmd.up


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, ctx):
        return self.commands.keys()


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name='s')(doco_cmd.status.main)
app.command(name='r')(doco_cmd.restart.main)
app.command(name='d')(doco_cmd.down.main)
app.command(name='u')(doco_cmd.up.main)
app.command(name='l')(doco_cmd.log.main)
app.command(name='backup')(doco_cmd.backup.main)
app.command(name='restore')(doco_cmd.restore.main)


@app.callback()
def main():
    """
    [b]doco[/] ([b]do[/]cker [b]co[/]mpose tool) is a command line tool for working with [i]docker compose[/] projects.
    Its core features are the colored status output and the backup functionality.
    """


if __name__ == "__main__":
    app()
