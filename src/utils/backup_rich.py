import os
import tempfile
import typing as t

import rich.tree

from src.utils.backup import BackupJob
from src.utils.rich import format_cmd_line
from src.utils.rich import Formatted
from src.utils.rich import rich_print_cmd
from src.utils.rsync import RsyncConfig
from src.utils.rsync import run_rsync_backup_with_hardlinks
from src.utils.rsync import run_rsync_without_delete


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
    new_backup_dir: str,
    old_backup_dir: t.Optional[str],
    content: str,
    target_file_name: str,
    dry_run: bool,
    rich_node: rich.tree.Tree,
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        source = os.path.join(tmp_dir, target_file_name)
        with open(source, "w", encoding="utf-8") as f:
            f.write(content)
        cmd = run_rsync_backup_with_hardlinks(
            config=rsync_config,
            source=source,
            new_backup=os.path.join(new_backup_dir, target_file_name),
            old_backup_dirs=[old_backup_dir] if old_backup_dir is not None else [],
            dry_run=dry_run,
            print_cmd_callback=rich_print_cmd,
        )
        rich_node.add(str(format_cmd_line(cmd)))


def do_backup_job(
    rsync_config: RsyncConfig,
    new_backup_dir: str,
    old_backup_dir: t.Optional[str],
    job: BackupJob,
    dry_run: bool,
    rich_node: rich.tree.Tree,
):
    if old_backup_dir is not None:
        old_backup_path = os.path.normpath(os.path.join(old_backup_dir, job.rsync_target_path))
        if not job.is_dir:
            old_backup_path = os.path.dirname(old_backup_path)
    else:
        old_backup_path = None
    cmd = run_rsync_backup_with_hardlinks(
        config=rsync_config,
        source=job.rsync_source_path,
        new_backup=os.path.join(new_backup_dir, job.rsync_target_path),
        old_backup_dirs=[old_backup_path] if old_backup_path is not None else [],
        dry_run=dry_run,
        print_cmd_callback=rich_print_cmd,
    )
    rich_node.add(str(format_cmd_line(cmd)))


def create_target_structure(
    rsync_config: RsyncConfig,
    new_backup_dir: str,
    jobs: t.Iterable[BackupJob],
    dry_run: bool,
    rich_node: rich.tree.Tree,
):
    """Create target directory structure at destination

    Required as long as remote rsync does not implement --mkpath
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
        cmd = run_rsync_without_delete(
            config=rsync_config,
            source=f"{tmp_dir}/",
            destination="",
            dry_run=dry_run,
            print_cmd_callback=rich_print_cmd,
        )
        rich_node.add(str(format_cmd_line(cmd)))
