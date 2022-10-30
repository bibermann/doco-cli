import rich.panel
import typer

from src.utils.rich import Formatted


class DocoError(Exception):
    def __init__(self, message: str, formatted: bool = False):
        Exception.__init__(self)
        rich.print(
            rich.panel.Panel(
                str(Formatted(message)) if not formatted else message,
                title="Error",
                title_align="left",
                border_style="red",
            )
        )
        raise typer.Exit(1)
