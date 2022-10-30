import dataclasses
import datetime
import os
import pathlib
import re
import typing as t

import pydantic
import rich.console
import rich.json
import rich.markup
import rich.panel
import rich.pretty
import rich.tree
import typer

from src.utils.backup import BACKUP_CONFIG_JSON
from src.utils.backup import BackupJob
from src.utils.backup import LAST_BACKUP_DIR_FILENAME
from src.utils.backup import load_last_backup_directory
from src.utils.backup import save_last_backup_directory
from src.utils.backup_rich import create_target_structure
from src.utils.backup_rich import do_backup_content
from src.utils.backup_rich import do_backup_job
from src.utils.backup_rich import format_do_backup
from src.utils.backup_rich import format_no_backup
from src.utils.cli import PROJECTS_ARGUMENT
from src.utils.cli import RUNNING_OPTION
from src.utils.common import dir_from_path
from src.utils.common import relative_path_if_below
from src.utils.compose_rich import ComposeProject
from src.utils.compose_rich import get_compose_projects
from src.utils.compose_rich import ProjectSearchOptions
from src.utils.compose_rich import rich_run_compose
from src.utils.exceptions_rich import DocoError
from src.utils.rich import Formatted
from src.utils.rsync import RsyncConfig

COMPOSE_CONFIG_YAML = "compose.yaml"


@dataclasses.dataclass
class BackupOptions:
    include_project_dir: bool
    include_read_only_volumes: bool
    volumes: list[str]
    live: bool
    dry_run: bool
    dry_run_verbose: bool


class BackupConfigServiceTask(pydantic.BaseModel):
    name: str
    backup_volumes: list[t.Tuple[str, str]] = []
    exclude_volumes: list[str] = []


class BackupConfigOptions(pydantic.BaseModel):
    live: bool
    include_project_dir: bool
    include_read_only_volumes: bool
    volume_patterns: list[str]


class BackupConfigTasks(pydantic.BaseModel):
    restart_project: bool = False
    create_last_backup_dir_file: t.Union[bool, str]
    backup_config: t.Union[bool, str]
    backup_compose_config: t.Union[bool, str]
    backup_project_dir: t.Union[bool, t.Tuple[str, str]]
    backup_services: list[BackupConfigServiceTask] = []


class BackupConfig(pydantic.BaseModel):
    backup_tool: str = "doco"
    project_path: str
    compose_file: str
    timestamp: datetime.datetime
    backup_dir: str
    last_backup_dir: t.Optional[str]
    rsync: RsyncConfig
    options: BackupConfigOptions
    tasks: BackupConfigTasks


def do_backup(
    project: ComposeProject,
    options: BackupOptions,
    config: BackupConfig,
    jobs: list[BackupJob],
    run_node: rich.tree.Tree,
):
    create_target_structure(
        rsync_config=project.doco_config.backup.rsync,
        new_backup_dir=config.backup_dir,
        jobs=jobs,
        dry_run=options.dry_run,
        rich_node=run_node,
    )

    if config.tasks.restart_project:
        rich_run_compose(
            project.dir, project.file, command=["down"], dry_run=options.dry_run, rich_node=run_node
        )

    if config.tasks.backup_config:
        do_backup_content(
            rsync_config=project.doco_config.backup.rsync,
            new_backup_dir=config.backup_dir,
            old_backup_dir=config.last_backup_dir,
            content=config.json(indent=4),
            target_file_name=BACKUP_CONFIG_JSON,
            dry_run=options.dry_run,
            rich_node=run_node,
        )

    if config.tasks.backup_compose_config:
        do_backup_content(
            rsync_config=project.doco_config.backup.rsync,
            new_backup_dir=config.backup_dir,
            old_backup_dir=config.last_backup_dir,
            content=project.config_yaml,
            target_file_name=COMPOSE_CONFIG_YAML,
            dry_run=options.dry_run,
            rich_node=run_node,
        )

    for job in jobs:
        do_backup_job(
            rsync_config=project.doco_config.backup.rsync,
            new_backup_dir=config.backup_dir,
            old_backup_dir=config.last_backup_dir,
            job=job,
            dry_run=options.dry_run,
            rich_node=run_node,
        )

    if config.tasks.restart_project:
        rich_run_compose(
            project.dir, project.file, command=["up", "-d"], dry_run=options.dry_run, rich_node=run_node
        )

    if not options.dry_run and config.tasks.create_last_backup_dir_file:
        save_last_backup_directory(project.dir, config.backup_dir)


def backup_project(  # noqa: C901 CFQ001 (too complex, max allowed length)
    project: ComposeProject, options: BackupOptions
):
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    project_name = project.config["name"]
    project_id_str = f"[b]{Formatted(project_name)}[/]"
    project_id_str += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"
    project_id = Formatted(project_id_str, True)

    now = datetime.datetime.now()
    new_backup_dir = os.path.join(project_name, f"backup-{now.strftime('%Y-%m-%d_%H.%M')}")
    old_backup_dir = load_last_backup_directory(project.dir)

    config = BackupConfig(
        project_path=os.path.abspath(project.dir),
        compose_file=project.file,
        timestamp=now,
        backup_dir=new_backup_dir,
        last_backup_dir=old_backup_dir,
        rsync=project.doco_config.backup.rsync,
        options=BackupConfigOptions(
            live=options.live,
            include_project_dir=options.include_project_dir,
            include_read_only_volumes=options.include_read_only_volumes,
            volume_patterns=options.volumes,
        ),
        tasks=BackupConfigTasks(
            create_last_backup_dir_file=LAST_BACKUP_DIR_FILENAME,
            backup_config=BACKUP_CONFIG_JSON,
            backup_compose_config=COMPOSE_CONFIG_YAML,
            backup_project_dir=options.include_project_dir,
        ),
    )
    jobs: list[BackupJob] = []

    tree = rich.tree.Tree(str(project_id))
    if old_backup_dir is None:
        tree.add(f"[i]Backup directory:[/] [b]{Formatted(new_backup_dir)}[/]")
    else:
        tree.add(
            f"[i]Backup directory:[/] [dim]{Formatted(old_backup_dir)}[/] => [b]{Formatted(new_backup_dir)}[/]"
        )
    backup_node = tree.add("[i]Backup items[/]")

    # Schedule config.json
    config_group = rich.console.Group(f"[green]{Formatted(BACKUP_CONFIG_JSON)}[/]")
    backup_node.add(config_group)

    # Schedule compose.yaml
    backup_node.add(f"[green]{Formatted(COMPOSE_CONFIG_YAML)}[/]")

    # Schedule project files
    job = BackupJob(source_path="", target_path="project-files", project_dir=project.dir, is_dir=True)
    if config.tasks.backup_project_dir:
        jobs.append(job)
        backup_node.add(str(format_do_backup(job)))
        config.tasks.backup_project_dir = (job.relative_source_path, job.relative_target_path)
    else:
        backup_node.add(str(format_no_backup(job, "project dir")))

    has_running_or_restarting = False

    # Schedule volumes
    volumes_included: t.Set[str] = set()
    for service_name, service in project.config["services"].items():
        state = next((s["State"] for s in project.ps if s["Service"] == service_name), "exited")
        if state in ("running", "restarting"):
            has_running_or_restarting = True

        s = backup_node.add(f"[b]{Formatted(service_name)}[/] [i]{Formatted(state)}[/]")
        service_task = BackupConfigServiceTask(name=service_name)
        config.tasks.backup_services.append(service_task)

        volumes = service.get("volumes", [])
        for volume in volumes:
            job = BackupJob(
                source_path=volume["source"],
                target_path=os.path.join("volumes", service_name, dir_from_path(volume["target"])),
                project_dir=project.dir,
                check_is_dir=True,
            )

            if options.include_project_dir and (
                relative_path_if_below(job.rsync_source_path) + "/"
            ).startswith(project.dir + "/"):
                s.add(str(format_no_backup(job, "already included", emphasize=False)))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue

            if job.rsync_source_path in volumes_included:
                s.add(str(format_no_backup(job, "already included", emphasize=False)))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue

            is_bind_mount = volume["type"] == "bind"
            if not is_bind_mount:
                s.add(str(format_no_backup(job, "no bind mount")))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue
            read_only = volume.get("read_only", False)
            if read_only and not options.include_read_only_volumes:
                s.add(str(format_no_backup(job, "read-only")))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue
            found = False
            for volume_regex in options.volumes:
                if re.search(volume_regex, job.rsync_source_path):
                    found = True
                    break
            if not found:
                s.add(str(format_no_backup(job, "expressions don't match")))
                service_task.exclude_volumes.append(job.rsync_source_path)
                continue

            jobs.append(job)
            s.add(str(format_do_backup(job)))
            service_task.backup_volumes.append((job.relative_source_path, job.relative_target_path))
            volumes_included.add(job.rsync_source_path)

        if len(volumes) == 0:
            s.add("[dim](no volumes)[/]")

    run_node = rich.tree.Tree("[i]Would run[/]")
    if options.dry_run_verbose:
        tree.add(run_node)

    config.tasks.restart_project = not options.live and has_running_or_restarting

    do_backup(project=project, options=options, config=config, jobs=jobs, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(config.json(indent=4)), expand=False, border_style="green")
            )

        rich.print(tree)


def volumes_callback(ctx: typer.Context, volumes: list[str]) -> list[str]:
    if ctx.resilient_parsing:
        return volumes
    try:
        [re.compile(pattern) for pattern in volumes]
    except re.error as e:
        raise typer.BadParameter(f"Invalid regex pattern {e.pattern!r}: {e}")
    return volumes


def main(  # noqa: CFQ002 (max arguments)
    projects: list[pathlib.Path] = PROJECTS_ARGUMENT,
    running: bool = RUNNING_OPTION,
    exclude_project_dir: bool = typer.Option(
        False, "-e", "--exclude-project-dir", help="Exclude project directory."
    ),
    include_ro: bool = typer.Option(False, "-r", "--include-ro", help="Also consider read-only volumes."),
    volume: list[str] = typer.Option(
        [r"^(?!/(bin|boot|dev|etc|lib\w*|proc|run|sbin|sys|tmp|usr|var)/)"],
        "--volume",
        "-v",
        callback=volumes_callback,
        help="Regex for volume selection, can be specified multiple times. "
        "Use -v [b yellow]'(?!)'[/] to exclude all volumes. "
        "Use -v [b yellow]^/path/[/] to only allow specified paths. "
        "[d]\\[default: (exclude many system directories)][/]",
        show_default=False,
    ),
    live: bool = typer.Option(False, "--live", help="Do not stop the services before backup."),
    verbose: bool = typer.Option(False, "--verbose", help="Print more details if --dry-run."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually backup, only show what would be done."
    ),
):
    """
    Backup projects.
    """

    if not (dry_run or os.geteuid() == 0):
        raise DocoError(
            "You need to have root privileges to do a backup.\n" "Please try again, this time using 'sudo'."
        )

    def check_rsync_config(rsync_config: RsyncConfig):
        if rsync_config.host == "" or rsync_config.module == "":
            raise DocoError(
                "You need to configure rsync to get a backup.\n"
                "Please see documentation for 'doco.config.json'."
            )

    for project in get_compose_projects(
        projects,
        ProjectSearchOptions(
            print_compose_errors=dry_run,
            only_running=running,
        ),
    ):
        check_rsync_config(project.doco_config.backup.rsync)
        backup_project(
            project=project,
            options=BackupOptions(
                include_project_dir=not exclude_project_dir,
                include_read_only_volumes=include_ro,
                volumes=volume,
                live=live,
                dry_run=dry_run,
                dry_run_verbose=verbose,
            ),
        )
