from utils.rsync import RsyncConfig
from utils.rsync import run_rsync_list


def get_backup_directory(rsync_config: RsyncConfig, project_name: str, backup_id: str) -> str:
    if backup_id.isnumeric():
        _, file_list = run_rsync_list(rsync_config, target=f"{project_name}/",
                                      dry_run=False)
        return sorted(
            [file for file in file_list if file.startswith('backup-')], reverse=True
        )[int(backup_id)]
    else:
        return f"backup-{backup_id}"
