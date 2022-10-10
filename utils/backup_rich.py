import rich
import rich.pretty
import rich.tree

from utils.doco_config import load_doco_config
from utils.rich import format_cmd_line
from utils.rich import Formatted
from utils.rsync import run_rsync_list


def list_services(dry_run: bool):
    doco_config = load_doco_config('.')
    cmd, file_list = run_rsync_list(doco_config.backup.rsync, target="", dry_run=dry_run)
    if dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))
    else:
        tree = rich.tree.Tree(f"[b]Services[/]")
        files = sorted([file for file in file_list if file != '.'])
        for i, file in enumerate(files):
            tree.add(f"[yellow]{Formatted(file)}[/]")
        rich.print(tree)


def list_backups(service: str, dry_run: bool):
    doco_config = load_doco_config('.')
    cmd, file_list = run_rsync_list(doco_config.backup.rsync, target=f"{service}/",
                                    dry_run=dry_run)
    if dry_run:
        rich.print(rich.tree.Tree(str(format_cmd_line(cmd))))
    else:
        tree = rich.tree.Tree(f"[b]{Formatted(service)}[/]")
        files = sorted([file[7:] for file in file_list if file.startswith('backup-')], reverse=True)
        for i, file in enumerate(files):
            tree.add(f"[yellow]{i}[/][dim]:[/] {Formatted(file)}")
        rich.print(tree)