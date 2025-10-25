#!/usr/bin/env python3
import json
import pathlib
import typing as t

import click
import typer.core

import src.utils.doco_config
from src.commands import backups as cmd_backups
from src.commands import down as cmd_down
from src.commands import log as cmd_log
from src.commands import restart as cmd_restart
from src.commands import status as cmd_status
from src.commands import up as cmd_up

__version__ = "2.2.2"


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, ctx: click.Context) -> t.List[str]:  # pylint: disable=unused-argument
        return list(self.commands.keys())


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name="s")(cmd_status.main)
app.command(name="u")(cmd_up.main)
app.command(name="d")(cmd_down.main)
app.command(name="r")(cmd_restart.main)
app.command(name="l")(cmd_log.main)
app.add_typer(cmd_backups.app, name="backups")


def version_callback(value: bool):
    if value:
        print(f"Doco CLI Version: {__version__}")
        raise typer.Exit()


def create_schema_callback(value: bool):
    if value:
        schema_filename = pathlib.Path("doco.config-schema.json")
        schema_filename.write_text(
            json.dumps(src.utils.doco_config.DocoConfig.model_json_schema(), indent=2) + "\n", encoding="utf-8"
        )
        print(f"{schema_filename} written.")

        config_filename = pathlib.Path("doco.config.toml")
        if not config_filename.exists():
            config_filename.write_text("# $schema: ./doco.config-schema.json", encoding="utf-8")
            print(f"Empty {config_filename} referencing the schema created.")

        raise typer.Exit()


@app.callback()
def main(
    _: t.Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version information and exit."
    ),
    _create_schema: t.Optional[bool] = typer.Option(
        False,
        "--create-schema",
        callback=create_schema_callback,
        help="Write config schema to current directory and exit.",
    ),
):
    """
    [b]doco[/] ([b]do[/]cker [b]co[/]mpose tool) is a command line tool
    for working with [i]docker compose[/] projects
    (pretty-printing status, creating backups using rsync, batch commands and more).
    """


if __name__ == "__main__":
    app()
