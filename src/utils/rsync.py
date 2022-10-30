import subprocess
import typing as t

import pydantic

from src.utils.common import print_cmd
from src.utils.common import PrintCmdCallable


class RsyncConfig(pydantic.BaseModel):
    rsh: t.Optional[str] = None
    host: str = ""
    module: str = ""
    root: str = "/"


class RsyncBaseOptions:
    def __init__(
        self,
        config: RsyncConfig,
    ):
        if config.host == "" or config.module == "":
            raise Exception("You need to configure rsync.")

        ssh_opts = ["-e", config.rsh] if config.rsh is not None else []
        self.opts = [*ssh_opts]
        self.host = config.host
        self.module = config.module
        self.root = config.root


class RsyncBackupOptions(RsyncBaseOptions):
    def __init__(
        self,
        config: RsyncConfig,
        delete_from_destination: bool,
        show_progress: bool = False,
        dry_run: bool = False,
    ):
        super().__init__(config)

        info_opts = [
            "-h",
            *(["--info=progress2"] if show_progress else []),
        ]
        backup_opts = [
            *(["--delete"] if delete_from_destination else []),
            # '--mkpath', # --mkpath supported only since 3.2.3
            "-z",
            *(["-n"] if dry_run else []),
        ]
        archive_opts = [
            "-a",
            # '-N', # -N (--crtimes) supported only on OS X apparently
            "--numeric-ids",
        ]
        self.opts.extend([*info_opts, *backup_opts, *archive_opts])


class RsyncListOptions(RsyncBaseOptions):
    def __init__(
        self,
        config: RsyncConfig,
    ):
        super().__init__(config)

        list_opts = [
            "--list-only",
        ]
        self.opts.extend([*list_opts])


def run_rsync_without_delete(
    config: RsyncConfig,
    source: str,
    destination: str,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(config=config, delete_from_destination=False)
    cmd = [
        "rsync",
        *opt.opts,
        "--",
        source,
        f"{opt.host}::{opt.module}{opt.root}/{destination}",
    ]
    if not dry_run:
        print_cmd_callback(cmd, None)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_incremental(
    config: RsyncConfig,
    source: str,
    destination: str,
    backup_dir: str,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(config=config, delete_from_destination=True)
    cmd = [
        "rsync",
        *opt.opts,
        "--backup-dir",
        f"{opt.root}/{backup_dir}",
        "--",
        source,
        f"{opt.host}::{opt.module}{opt.root}/{destination}",
    ]
    if not dry_run:
        print_cmd_callback(cmd, None)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_with_hardlinks(
    config: RsyncConfig,
    source: str,
    new_backup: str,
    old_backup_dirs: list[str],
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(config=config, delete_from_destination=True)
    for old_backup_dir in old_backup_dirs:
        opt.opts.extend(["--link-dest", f"{opt.root}/{old_backup_dir}"])
    cmd = [
        "rsync",
        *opt.opts,
        "--",
        source,
        f"{opt.host}::{opt.module}{opt.root}/{new_backup}",
    ]
    if not dry_run:
        print_cmd_callback(cmd, None)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_download_incremental(
    config: RsyncConfig,
    source: str,
    destination: str,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(config=config, delete_from_destination=True)
    cmd = [
        "rsync",
        *opt.opts,
        "--",
        f"{opt.host}::{opt.module}{opt.root}/{source}",
        destination,
    ]
    if not dry_run:
        print_cmd_callback(cmd, None)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_list(
    config: RsyncConfig,
    target: str,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> t.Tuple[list[str], list[str]]:
    opt = RsyncListOptions(config=config)
    cmd = [
        "rsync",
        *opt.opts,
        "--",
        f"{opt.host}::{opt.module}{opt.root}/{target}",
    ]
    file_list = []
    if not dry_run:
        print_cmd_callback(cmd, None)
        result = subprocess.run(
            cmd, capture_output=True, encoding="utf-8", universal_newlines=True, check=True
        )
        for line in result.stdout.split("\n"):
            if len(line) >= 5:
                file_list.append(" ".join(line.split()[4:]))
    return cmd, file_list
