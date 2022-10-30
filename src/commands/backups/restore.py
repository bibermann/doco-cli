import dataclasses
import itertools
import json
import os
import pathlib
import tempfile
import typing as t

import rich.json
import rich.panel
import rich.tree
import typer

from src.utils.backup import BACKUP_CONFIG_JSON
from src.utils.cli import PROJECTS_ARGUMENT
from src.utils.cli import RUNNING_OPTION
from src.utils.compose_rich import ComposeProject
from src.utils.compose_rich import get_compose_projects
from src.utils.compose_rich import ProjectSearchOptions
from src.utils.compose_rich import rich_run_compose
from src.utils.exceptions_rich import DocoError
from src.utils.restore import get_backup_directory
from src.utils.restore import RestoreJob
from src.utils.restore_rich import create_target_structure
from src.utils.restore_rich import do_restore_job
from src.utils.restore_rich import list_backups
from src.utils.rich import Formatted
from src.utils.rich import rich_print_cmd
from src.utils.rsync import RsyncConfig
from src.utils.rsync import run_rsync_download_incremental
from src.utils.validators import project_name_callback


@dataclasses.dataclass
class RestoreOptions:
    project_name: str
    backup: str
    dry_run: bool
    dry_run_verbose: bool


@dataclasses.dataclass
class RestoreConfigTasks:
    restart_project: bool = False


@dataclasses.dataclass
class RestoreConfig:
    tasks: RestoreConfigTasks


def do_restore(
    project: ComposeProject,
    options: RestoreOptions,
    config: RestoreConfig,
    jobs: list[RestoreJob],
    run_node: rich.tree.Tree,
):
    create_target_structure(jobs=jobs, dry_run=options.dry_run, rich_node=run_node)

    if config.tasks.restart_project:
        rich_run_compose(
            project.dir, project.file, command=["down"], dry_run=options.dry_run, rich_node=run_node
        )

    for job in jobs:
        do_restore_job(
            rsync_config=project.doco_config.backup.rsync, job=job, dry_run=options.dry_run, rich_node=run_node
        )

    if config.tasks.restart_project:
        rich_run_compose(
            project.dir, project.file, command=["up", "-d"], dry_run=options.dry_run, rich_node=run_node
        )


def restore_project(  # noqa: C901 CFQ001 (too complex, max allowed length)
    project: ComposeProject, options: RestoreOptions
):
    # pylint: disable=too-many-locals
    backup_dir = get_backup_directory(
        project.doco_config.backup.rsync,
        project_name=options.project_name,
        backup_id=options.backup,
        print_cmd_callback=rich_print_cmd,
    )

    backup_config: t.Any = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = os.path.join(tmp_dir, BACKUP_CONFIG_JSON)
        run_rsync_download_incremental(
            project.doco_config.backup.rsync,
            source=f"{options.project_name}/{backup_dir}/{BACKUP_CONFIG_JSON}",
            destination=os.path.join(tmp_dir, BACKUP_CONFIG_JSON),
            dry_run=False,
            print_cmd_callback=rich_print_cmd,
        )
        with open(config_path, encoding="utf-8") as f:
            backup_config = json.load(f)

    project_name = options.project_name
    project_id_str = f"[b]{Formatted(project_name)}[/]"
    project_id_str += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"
    project_id = Formatted(project_id_str, True)

    tree = rich.tree.Tree(str(project_id))
    backup_dir_node = tree.add(f"[i]Backup directory:[/] [b]{Formatted(backup_dir)}[/]")

    if backup_config.get("backup_tool", "") != "doco":
        config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
        backup_dir_node.add(config_group)

        config_group.renderables.append(
            rich.panel.Panel(
                rich.json.JSON(json.dumps(backup_config, indent=4)), expand=False, border_style="green"
            )
        )

        raise DocoError("The config does not look like a doco config.")

    backup_node = tree.add("[i]Backup items[/]")

    backup_volumes = list(
        itertools.chain(
            *[
                service.get("backup_volumes", [])
                for service in backup_config.get("tasks", {}).get("backup_services", [])
            ]
        )
    )

    has_running_or_restarting = False
    for service_name, _ in project.config.get("services", {}).items():
        state = next((s["State"] for s in project.ps if s["Service"] == service_name), "exited")
        if state in ("running", "restarting"):
            has_running_or_restarting = True

    config = RestoreConfig(
        tasks=RestoreConfigTasks(),
    )
    jobs: list[RestoreJob] = []

    backup_project_dir = backup_config.get("tasks", {}).get("backup_project_dir", True)
    if backup_project_dir:
        jobs.append(
            RestoreJob(
                source_path="project_files" if isinstance(backup_project_dir, bool) else backup_project_dir[1],
                target_path="." if isinstance(backup_project_dir, bool) else backup_project_dir[0],
                project_dir=project.dir,
            )
        )

    for backup_volumes_item in backup_volumes:
        jobs.append(
            RestoreJob(
                source_path=backup_volumes_item[1], target_path=backup_volumes_item[0], project_dir=project.dir
            )
        )

    for job in jobs:
        if os.path.exists(job.absolute_target_path):
            action = "[red](override)[/]"
        else:
            action = "(create)"
        backup_node.add(
            f"{job.display_source_path} [dim]->[/] [dark_orange]{job.display_target_path}[/] {action}"
        )

    run_node = rich.tree.Tree("[i]Would run[/]")
    if options.dry_run_verbose:
        tree.add(run_node)

    config.tasks.restart_project = has_running_or_restarting

    do_restore(project=project, options=options, config=config, jobs=jobs, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
            backup_dir_node.add(config_group)

            config_group.renderables.append(
                rich.panel.Panel(
                    rich.json.JSON(json.dumps(backup_config, indent=4)), expand=False, border_style="green"
                )
            )

        rich.print(tree)


def get_project_name(project_name: t.Optional[str], project: ComposeProject) -> str:
    if project_name is not None:
        return project_name
    if "name" in project.config:
        return project.config["name"]
    return os.path.basename(os.path.abspath(project.dir))


def main(  # noqa: CFQ002 (max arguments)
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    running: bool = RUNNING_OPTION,
    name: t.Optional[str] = typer.Option(
        None, callback=project_name_callback, help="Override project name. Using directory name if not given."
    ),
    do_list: bool = typer.Option(False, "-l", "--list", help="List backups instead of restoring a backup."),
    backup: str = typer.Option("0", "--backup", "-b", help="Backup index or name."),
    verbose: bool = typer.Option(False, "--verbose", help="Print more details if --dry-run."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually restore a backup, only show what would be done."
    ),
):
    """
    Restore project backups.
    """

    if not (dry_run or os.geteuid() == 0):
        raise DocoError(
            "You need to have root privileges to restore a backup.\n"
            "Please try again, this time using 'sudo'."
        )

    compose_projects = list(
        get_compose_projects(
            projects,
            ProjectSearchOptions(
                print_compose_errors=dry_run,
                only_running=running,
                allow_empty=True,
            ),
        )
    )

    if name is not None and len(compose_projects) != 1:
        raise DocoError(
            "You cannot specify '[b green]-p[/]' / '[b bright_cyan]--project[/]' "
            "when restoring more than one project.",
            formatted=True,
        )

    def check_rsync_config(rsync_config: RsyncConfig):
        if rsync_config.host == "" or rsync_config.module == "":
            raise DocoError(
                "You need to configure rsync to get a backup.\n"
                "Please see documentation for 'doco.config.json'."
            )

    if do_list:
        for compose_project in compose_projects:
            check_rsync_config(compose_project.doco_config.backup.rsync)
            list_backups(
                project_name=get_project_name(name, compose_project), doco_config=compose_project.doco_config
            )
    else:
        for compose_project in compose_projects:
            check_rsync_config(compose_project.doco_config.backup.rsync)
            restore_project(
                project=compose_project,
                options=RestoreOptions(
                    project_name=get_project_name(name, compose_project),
                    backup=backup,
                    dry_run=dry_run,
                    dry_run_verbose=verbose,
                ),
            )
