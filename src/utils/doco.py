import dataclasses
import os
import typing as t

import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree

from .compose_rich import ComposeProject
from .rich import Formatted


@dataclasses.dataclass
class ProjectInfo:
    has_running_or_restarting: bool
    all_running: bool
    run_node: rich.tree.Tree


def do_project_cmd(project: ComposeProject, dry_run: bool, cmd_task: t.Callable[[ProjectInfo], None]):
    project_name = project.config["name"]
    project_id = f"[b]{Formatted(project_name)}[/]"
    project_id += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"

    tree = rich.tree.Tree(project_id)

    has_running_or_restarting = False
    all_running = True

    for service_name, _ in project.config["services"].items():
        state = next((s["State"] for s in project.ps if s["Service"] == service_name), "exited")

        if state in ("running", "restarting"):
            has_running_or_restarting = True

        if state != "running":
            all_running = False

        tree.add(f"[b]{Formatted(service_name)}[/] [i]{Formatted(state)}[/]")

    run_node = rich.tree.Tree("[i]Would run[/]")
    if dry_run:
        tree.add(run_node)

    cmd_task(
        ProjectInfo(
            has_running_or_restarting=has_running_or_restarting,
            all_running=all_running,
            run_node=run_node,
        )
    )

    if len(run_node.children) == 0:
        run_node.add("[dim](nothing)[/]")

    if dry_run:
        rich.print(tree)
