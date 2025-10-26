import os
import subprocess
import tempfile
import typing as t

from src.utils.backup import BackupJob
from src.utils.common import PrintCmdData
from src.utils.doco_config import DocoBackupStructureConfig
from src.utils.rich import Formatted
from src.utils.rich import rich_print_cmd
from src.utils.rich import RichAbortCmd
from src.utils.rsync import RsyncConfig
from src.utils.rsync import run_rsync_backup_incremental
from src.utils.rsync import run_rsync_backup_with_hardlinks
from src.utils.rsync import run_rsync_without_delete
from src.utils.system import chown_given_strings


def format_do_backup(job: BackupJob) -> Formatted:
    return Formatted(
        f"[green][b]{Formatted(job.display_source_path)}[/] "
        f"[dim]as[/] {Formatted(job.display_target_path)}[/]",
        True,
    )


def format_no_backup(job: BackupJob, reason: str, emphasize: bool = True) -> Formatted:
    if emphasize:
        return Formatted(f"[red]{Formatted(job.display_source_path)} [dim]({Formatted(reason)})[/][/]", True)
    return Formatted(f"{Formatted(job.display_source_path)} [dim]({Formatted(reason)})[/]", True)


def do_backup_content(  # noqa: CFQ002 (max arguments)
    rsync_config: RsyncConfig,
    structure_config: DocoBackupStructureConfig,
    new_backup_dir: str,
    old_backup_dir: t.Optional[str],
    content: str,
    target_file_name: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool,
    cmds: list[PrintCmdData],
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        source = os.path.join(tmp_dir, target_file_name)
        with open(source, "w", encoding="utf-8") as f:
            f.write(content)
        chown_given_strings(source, structure_config.uid, structure_config.gid)
        try:
            cmd = run_rsync_backup_with_hardlinks(
                config=rsync_config,
                source=source,
                new_backup=os.path.join(new_backup_dir, target_file_name),
                old_backup_dirs=[old_backup_dir] if old_backup_dir is not None else [],
                project_for_filter="",
                show_progress=show_progress,
                verbose=verbose,
                dry_run=dry_run,
                print_cmd_callback=rich_print_cmd,
            )
        except subprocess.CalledProcessError as e:
            raise RichAbortCmd(e) from e
        cmds.append(PrintCmdData(cmd=cmd))


def do_copy_content(  # noqa: CFQ002 (max arguments)
    rsync_config: RsyncConfig,
    structure_config: DocoBackupStructureConfig,
    backup_dir: str,
    content: str,
    target_file_name: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool,
    cmds: list[PrintCmdData],
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        source = os.path.join(tmp_dir, target_file_name)
        with open(source, "w", encoding="utf-8") as f:
            f.write(content)
        chown_given_strings(source, structure_config.uid, structure_config.gid)
        try:
            cmd = run_rsync_without_delete(
                config=rsync_config,
                source=source,
                destination=os.path.join(backup_dir, target_file_name),
                project_for_filter="",
                show_progress=show_progress,
                verbose=verbose,
                dry_run=dry_run,
                print_cmd_callback=rich_print_cmd,
            )
        except subprocess.CalledProcessError as e:
            raise RichAbortCmd(e) from e
        cmds.append(PrintCmdData(cmd=cmd))


def do_backup_job(  # noqa: CFQ002 (max arguments)
    rsync_config: RsyncConfig,
    new_backup_dir: str,
    old_backup_dir: t.Optional[str],
    job: BackupJob,
    project_for_filter: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool,
    cmds: list[PrintCmdData],
):
    if old_backup_dir is not None:
        old_backup_path = os.path.normpath(os.path.join(old_backup_dir, job.rsync_target_path))
        if not job.is_dir:
            old_backup_path = os.path.dirname(old_backup_path)
    else:
        old_backup_path = None
    try:
        cmd = run_rsync_backup_with_hardlinks(
            config=rsync_config,
            source=job.rsync_source_path,
            new_backup=os.path.join(new_backup_dir, job.rsync_target_path),
            old_backup_dirs=[old_backup_path] if old_backup_path is not None else [],
            project_for_filter=project_for_filter,
            show_progress=show_progress,
            verbose=verbose,
            dry_run=dry_run,
            print_cmd_callback=rich_print_cmd,
        )
    except subprocess.CalledProcessError as e:
        raise RichAbortCmd(e) from e
    cmds.append(PrintCmdData(cmd=cmd))


def do_incremental_backup_job(  # noqa: CFQ002 (max arguments)
    rsync_config: RsyncConfig,
    backup_dir: str,
    incremental_backup_dir: str,
    job: BackupJob,
    project_for_filter: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool,
    cmds: list[PrintCmdData],
):
    try:
        cmd = run_rsync_backup_incremental(
            config=rsync_config,
            source=job.rsync_source_path,
            destination=os.path.join(backup_dir, job.rsync_target_path),
            backup_dir=os.path.join(incremental_backup_dir, job.rsync_target_path),
            project_for_filter=project_for_filter,
            show_progress=show_progress,
            verbose=verbose,
            dry_run=dry_run,
            print_cmd_callback=rich_print_cmd,
        )
    except subprocess.CalledProcessError as e:
        raise RichAbortCmd(e) from e
    cmds.append(PrintCmdData(cmd=cmd))


def create_target_structure(  # noqa: CFQ002 (max arguments)
    rsync_config: RsyncConfig,
    structure_config: DocoBackupStructureConfig,
    new_backup_dir: str,
    jobs: t.Iterable[BackupJob],
    show_progress: bool,
    verbose: bool,
    dry_run: bool,
    cmds: list[PrintCmdData],
):
    """Create target directory structure at destination

    Required as long as remote rsync does not implement --mkpath
    But maybe even then, with this function we have the possibility to chown the directories.
    """

    paths = set(
        os.path.dirname(os.path.normpath(os.path.join(new_backup_dir, job.rsync_target_path))) for job in jobs
    )
    leafs = [
        leaf
        for leaf in paths
        if leaf != "" and next((path for path in paths if path.startswith(f"{leaf}/")), None) is None
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        for leaf in leafs:
            os.makedirs(os.path.join(tmp_dir, leaf))
        for root, _, _ in os.walk(tmp_dir):
            chown_given_strings(root, structure_config.uid, structure_config.gid)
        try:
            cmd = run_rsync_without_delete(
                config=rsync_config,
                source=f"{tmp_dir}/",
                destination="",
                project_for_filter="",
                show_progress=show_progress,
                verbose=verbose,
                dry_run=dry_run,
                print_cmd_callback=rich_print_cmd,
            )
        except subprocess.CalledProcessError as e:
            raise RichAbortCmd(e) from e
        cmds.append(PrintCmdData(cmd=cmd))
