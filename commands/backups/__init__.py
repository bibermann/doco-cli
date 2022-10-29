import typer.core

from . import create as cmd_create
from . import raw as cmd_raw
from . import restore as cmd_restore


class NaturalOrderGroup(typer.core.TyperGroup):
    def list_commands(self, _):
        return self.commands.keys()


app = typer.Typer(
    cls=NaturalOrderGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)

app.command(name="create")(cmd_create.main)
app.command(name="restore")(cmd_restore.main)
app.add_typer(cmd_raw.app, name="raw")


@app.callback()
def main():
    """
    Create, restore, download or list backups.
    """
