from utils.backup import BackupJob
from utils.rich import Formatted


def format_do_backup(job: BackupJob) -> Formatted:
    return Formatted(
        f"[green][b]{Formatted(job.display_source_path)}[/] [dim]as[/] {Formatted(job.display_target_path)}[/]",
        True)


def format_no_backup(job: BackupJob, reason: str, emphasize: bool = True) -> Formatted:
    if emphasize:
        return Formatted(f"[red]{Formatted(job.display_source_path)} [dim]({Formatted(reason)})[/][/]", True)
    else:
        return Formatted(f"{Formatted(job.display_source_path)} [dim]({Formatted(reason)})[/]", True)
