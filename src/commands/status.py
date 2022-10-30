import dataclasses
import os
import pathlib
import re
import typing as t

import rich.box
import rich.markup
import rich.table
import rich.tree
import typer

from src.utils.cli import PROJECTS_ARGUMENT
from src.utils.cli import RUNNING_OPTION
from src.utils.common import relative_path_if_below
from src.utils.compose_rich import ComposeProject
from src.utils.compose_rich import get_compose_projects
from src.utils.compose_rich import ProjectSearchOptions
from src.utils.doco_config import TextSubstitutions
from src.utils.rich import Formatted


def create_table(alternate_bg: bool) -> rich.table.Table:
    return rich.table.Table(
        title_justify="left",
        style="dim",
        header_style="i",
        box=rich.box.SQUARE,
        row_styles=["on grey7", ""] if alternate_bg else None,
    )


def colored_container_state(state: str) -> Formatted:
    if state == "running":
        return Formatted(f"[b green]{Formatted(state)}[/]", True)
    if state in ("exited", "dead"):
        return Formatted(f"[b red]{Formatted(state)}[/]", True)
    return Formatted(f"[b yellow]{Formatted(state)}[/]", True)


def dim_path(path: str, dimmed_prefix: str, bold: bool = False) -> Formatted:
    if path.startswith(dimmed_prefix):
        return Formatted(
            f"[dim]{Formatted(dimmed_prefix)}[/]{'[b]' if bold else ''}"
            f"{Formatted(path[len(dimmed_prefix):])}"
            f"{'[/]' if bold else ''}",
            True,
        )
    return Formatted(f"{'[b]' if bold else ''}" f"{Formatted(path)}" f"{'[/]' if bold else ''}", True)


def colored_path(
    path: str,
    text_substitutions: t.Optional[list[TextSubstitutions]] = None,
    dimmed_prefix: t.Optional[str] = None,
) -> Formatted:
    formatted = path
    for text_substitution in text_substitutions if text_substitutions is not None else []:
        formatted = re.sub(text_substitution.pattern, text_substitution.replace, formatted)
    if formatted != path:
        return Formatted(formatted, True)
    return (
        dim_path(path, dimmed_prefix=dimmed_prefix, bold=True)
        if dimmed_prefix is not None
        else Formatted(f"[b]{Formatted(path)}[/]", True)
    )


def colored_readonly(text: t.Union[str, Formatted], read_only: bool, is_bind_mount: bool) -> Formatted:
    text = Formatted(text)
    ro_text = text if read_only else Formatted(f"[dark_orange]{text}[/]", True)
    return ro_text if is_bind_mount else Formatted(f"[dim]{ro_text}[/]", True)


def colored_image(image: str) -> Formatted:
    if ":" not in image:
        image += ":latest"
    return Formatted(
        re.sub(
            r"^(docker.io/)?([^:]*):(.*)",
            r"[bright_blue][dim]\1[/][b]\2[/][dim]:[/]\3[/]",
            str(Formatted(image)),
        ),
        True,
    )


def colored_dockerfile(dockerfile: str, dimmed_prefix: str) -> Formatted:
    formatted = str(dim_path(dockerfile, dimmed_prefix=dimmed_prefix))
    formatted = re.sub(r"^(.*)Dockerfile(.*)$", r"[bright_blue]\1[dim]Dockerfile[/]\2[/]", formatted)
    if formatted != dockerfile:
        return Formatted(formatted, True)
    return Formatted(f"[bright_blue]{Formatted(dockerfile)}[/]", True)


def colored_key_value(  # noqa: CFQ004 (max returns amount)
    text: t.Union[str, Formatted], key: str, value: str
) -> Formatted:
    text = str(Formatted(text))
    if text[-1:] == "\n":
        text = text[:-1]
    if value.lower() in ("true", "yes", "on"):
        return Formatted(f"[green]{text}[/]", True)
    if value.lower() in ("false", "no", "off"):
        return Formatted(f"[red]{text}[/]", True)
    if value.isnumeric():
        return Formatted(f"[bright_blue]{text}[/]", True)
    if re.search(r"(?:\b|_)(?:pw|pass|password|token|secret)(?:\b|_)", key.lower()):
        return Formatted(f"[dim dark_orange]{text}[/]", True)
    return Formatted(text.replace(",", "[b white],[/]"), True)


def colored_port_mapping(mapping: t.Tuple[str, str]) -> Formatted:
    return Formatted(f"{mapping[0]}[dim]:{mapping[1]}[/]", True)


@dataclasses.dataclass
class PrintOptions:
    print_path: bool
    output_build: bool
    list_environment: bool
    list_volumes: int

    align_right: bool
    alternate_rows: bool


def print_project(  # noqa: C901 CFQ001 (too complex, max allowed length)
    project: ComposeProject,
    options: PrintOptions,
):
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    justify: rich.console.JustifyMethod = "left"
    if options.align_right:
        justify = "right"

    project_id_str = f"[b]{Formatted(project.config['name'])}[/]"
    if options.print_path:
        project_id_str += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"
    project_id = Formatted(project_id_str, True)
    tree = rich.tree.Tree(str(project_id))

    for service_name, service in project.config["services"].items():  # pylint: disable=too-many-nested-blocks
        state = next((s["State"] for s in project.ps if s["Service"] == service_name), "exited")
        is_image = "image" in service
        source = (
            colored_image(service["image"])
            if is_image
            else colored_dockerfile(
                relative_path_if_below(
                    os.path.join(service["build"]["context"], service["build"]["dockerfile"])
                ),
                project.dir + "/",
            )
        )

        ports = Formatted("", True)
        if "ports" in service:
            ports = Formatted(
                " ".join(str(colored_port_mapping((p["published"], p["target"]))) for p in service["ports"]),
                True,
            )

        service_line = [
            str(colored_container_state(state)),
            f"[b]{Formatted(service_name)}[/]",
            str(ports),
            str(source),
        ]
        s = tree.add(" ".join(z for z in service_line if z != ""))

        if options.output_build and not is_image:
            build_context = dim_path(
                relative_path_if_below(service["build"]["context"]) + "/", dimmed_prefix=project.dir + "/"
            )
            s.add(f"[i]Build context:[/] {build_context}")

        if options.output_build and not is_image and "args" in service["build"]:
            table = create_table(alternate_bg=options.alternate_rows and justify == "left")
            s.add(table)
            table.add_column("Build argument", no_wrap=True, justify=justify)
            table.add_column("Value")
            for arg, value in service["build"]["args"].items():
                table.add_row(
                    str(colored_key_value(arg, key=arg, value=value))
                    if value != ""
                    else f"[dim]{Formatted(arg)}[/]",
                    str(colored_key_value(value, key=arg, value=value)),
                )

        if options.list_environment and "environment" in service:
            table = create_table(alternate_bg=options.alternate_rows and justify == "left")
            s.add(table)
            table.add_column("Environment variable", no_wrap=True, justify=justify)
            table.add_column("Value")
            for env, value in service["environment"].items():
                table.add_row(
                    str(colored_key_value(env, key=env, value=value))
                    if value != ""
                    else f"[dim]{Formatted(env)}[/]",
                    str(colored_key_value(value, key=env, value=value)),
                )

        if options.list_volumes >= 1 and "volumes" in service:
            table = create_table(alternate_bg=options.alternate_rows)
            s.add(table)
            table.add_column("Volume")
            table.add_column("Container path")
            table.add_column("ro/rw")
            for volume in service["volumes"]:
                read_only = volume.get("read_only", False)
                is_volume_mount = volume["type"] == "volume"
                is_bind_mount = volume["type"] == "bind"
                is_dir = False
                if is_volume_mount:
                    source_volume = Formatted(volume["source"])
                elif is_bind_mount:
                    is_dir = os.path.isdir(volume["source"])
                    output_config = project.doco_config.output
                    source_volume = colored_path(
                        relative_path_if_below(volume["source"]) + ("/" if is_dir else ""),
                        text_substitutions=output_config.text_substitutions.bind_mount_volume_path,
                        dimmed_prefix=project.dir,
                    )
                else:
                    source_volume = Formatted(
                        f"{Formatted(volume['source'])} [dim]({Formatted(volume['type'])})[/]", True
                    )
                files = rich.tree.Tree(str(colored_readonly(source_volume, read_only, is_bind_mount)))
                if (
                    options.list_volumes >= 2
                    and volume["source"].startswith("/")
                    and os.path.isdir(volume["source"])
                ):
                    try:
                        for f in sorted(os.listdir(volume["source"])):
                            if os.path.isdir(os.path.join(volume["source"], f)):
                                files.add(f"[yellow]{Formatted(f)}/[/]")
                            else:
                                files.add(str(Formatted(f)))
                    except PermissionError:
                        pass
                table.add_row(
                    files,
                    str(
                        colored_readonly(volume["target"] + ("/" if is_dir else ""), read_only, is_bind_mount)
                    ),
                    str(colored_readonly("ro" if read_only else "rw", read_only, is_bind_mount)),
                )

    rich.print(tree)


DETAILS_GROUP = {"rich_help_panel": "Content detail Options"}
FORMATTING_GROUP = {"rich_help_panel": "Formatting Options"}


def main(  # noqa: CFQ002 (max arguments)
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    running: bool = RUNNING_OPTION,
    path: bool = typer.Option(False, "--path", "-p", **DETAILS_GROUP, help="Print path of compose file."),
    build: bool = typer.Option(
        False, "--build", "-b", **DETAILS_GROUP, help="Output build context and arguments."
    ),
    envs: bool = typer.Option(False, "--envs", "-e", **DETAILS_GROUP, help="List environment variables."),
    volumes: int = typer.Option(
        0, "--volumes", "-v", count=True, **DETAILS_GROUP, help="List volumes (use -vv to also list content)."
    ),
    all_details: int = typer.Option(
        0, "--all", "-a", count=True, **DETAILS_GROUP, help="Like -pbev (use -aa for -pbevv)."
    ),
    align_right: bool = typer.Option(False, "--right", **FORMATTING_GROUP, help="Right-align variable names."),
    alternate_rows: bool = typer.Option(
        False, "--zebra", **FORMATTING_GROUP, help="Alternate row colors in tables."
    ),
):
    """
    Print status of projects.
    """

    for project in get_compose_projects(
        projects,
        ProjectSearchOptions(
            print_compose_errors=True,
            only_running=running,
        ),
    ):
        print_project(
            project=project,
            options=PrintOptions(
                print_path=all_details >= 1 or path,
                output_build=all_details >= 1 or build,
                list_environment=all_details >= 1 or envs,
                list_volumes=max(all_details, volumes),
                align_right=align_right,
                alternate_rows=alternate_rows,
            ),
        )
