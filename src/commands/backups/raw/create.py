import dataclasses
import datetime
import os
import pathlib
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
from src.utils.bbak import BbakContextObject
from src.utils.common import dir_from_path
from src.utils.completers import PathCompleter
from src.utils.doco_config import DocoConfig
from src.utils.exceptions_rich import DocoError
from src.utils.rich import Formatted
from src.utils.rsync import RsyncConfig
from src.utils.validators import project_name_callback


@dataclasses.dataclass
class BackupOptions:
    workdir: str
    paths: list[str]
    dry_run: bool
    dry_run_verbose: bool


class BackupConfigTasks(pydantic.BaseModel):
    create_last_backup_dir_file: t.Union[bool, str]
    backup_config: t.Union[bool, str]
    backup_paths: list[t.Tuple[str, str]] = []


class BackupConfig(pydantic.BaseModel):
    backup_tool: str = "bbak"
    work_dir: str
    timestamp: datetime.datetime
    backup_dir: str
    last_backup_dir: t.Optional[str]
    rsync: RsyncConfig
    tasks: BackupConfigTasks


def do_backup(
    options: BackupOptions,
    config: BackupConfig,
    jobs: list[BackupJob],
    doco_config: DocoConfig,
    run_node: rich.tree.Tree,
):
    create_target_structure(
        rsync_config=doco_config.backup.rsync,
        new_backup_dir=config.backup_dir,
        jobs=jobs,
        dry_run=options.dry_run,
        rich_node=run_node,
    )

    if config.tasks.backup_config:
        do_backup_content(
            rsync_config=doco_config.backup.rsync,
            new_backup_dir=config.backup_dir,
            old_backup_dir=config.last_backup_dir,
            content=config.json(indent=4),
            target_file_name=BACKUP_CONFIG_JSON,
            dry_run=options.dry_run,
            rich_node=run_node,
        )

    for job in jobs:
        do_backup_job(
            rsync_config=doco_config.backup.rsync,
            new_backup_dir=config.backup_dir,
            old_backup_dir=config.last_backup_dir,
            job=job,
            dry_run=options.dry_run,
            rich_node=run_node,
        )

    if not options.dry_run and config.tasks.create_last_backup_dir_file:
        assert isinstance(config.tasks.create_last_backup_dir_file, str)
        save_last_backup_directory(
            options.workdir, config.backup_dir, file_name=config.tasks.create_last_backup_dir_file
        )


def backup_files(project_name: str, options: BackupOptions, doco_config: DocoConfig):
    project_id = f"[b]{Formatted(project_name)}[/]"

    now = datetime.datetime.now()
    new_backup_dir = os.path.join(project_name, f"backup-{now.strftime('%Y-%m-%d_%H.%M')}")
    old_backup_dir = load_last_backup_directory(options.workdir)

    config = BackupConfig(
        work_dir=os.path.abspath(options.workdir),
        timestamp=now,
        backup_dir=new_backup_dir,
        last_backup_dir=old_backup_dir,
        rsync=doco_config.backup.rsync,
        tasks=BackupConfigTasks(
            create_last_backup_dir_file=project_name + LAST_BACKUP_DIR_FILENAME,
            backup_config=BACKUP_CONFIG_JSON,
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

    # Schedule paths
    for path in options.paths:
        job = BackupJob(
            source_path=os.path.abspath(path),
            target_path=os.path.join("files", dir_from_path(os.path.abspath(path))),
            project_dir=options.workdir,
            check_is_dir=True,
        )

        jobs.append(job)
        backup_node.add(str(format_do_backup(job)))
        config.tasks.backup_paths.append((job.relative_source_path, job.relative_target_path))

    run_node = rich.tree.Tree("[i]Would run[/]")
    if options.dry_run_verbose:
        tree.add(run_node)

    do_backup(options=options, config=config, jobs=jobs, doco_config=doco_config, run_node=run_node)

    if options.dry_run:
        if options.dry_run_verbose:
            config_group.renderables.append(
                rich.panel.Panel(rich.json.JSON(config.json(indent=4)), expand=False, border_style="green")
            )

        rich.print(tree)


def main(
    ctx: typer.Context,
    project: str = typer.Argument(
        ..., callback=project_name_callback, help="Target project to write backups to."
    ),
    paths: list[pathlib.Path] = typer.Argument(
        ...,
        shell_complete=PathCompleter().__call__,
        exists=True,
        help="Paths to backup (not relative to --workdir but to the caller's CWD).",
        show_default=False,
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Print more details if --dry-run."),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Do not actually backup, only show what would be done."
    ),
):
    """
    Backup files and directories.
    """

    obj: BbakContextObject = ctx.obj

    if not (dry_run or os.geteuid() == 0):
        raise DocoError(
            "You need to have root privileges to do a backup.\n" "Please try again, this time using 'sudo'."
        )

    if obj.doco_config.backup.rsync.host == "" or obj.doco_config.backup.rsync.module == "":
        raise DocoError(
            "You need to configure rsync to get a backup.\n"
            "You may want to adjust '[b green]-w[/]' / '[b bright_cyan]--workdir[/]'.\n"
            "Please see documentation for 'doco.config.json'.",
            formatted=True,
        )

    backup_files(
        project_name=project,
        options=BackupOptions(
            workdir=obj.workdir,
            paths=list(map(str, paths)),
            dry_run=dry_run,
            dry_run_verbose=verbose,
        ),
        doco_config=obj.doco_config,
    )
