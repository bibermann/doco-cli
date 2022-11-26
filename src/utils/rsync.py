import re
import subprocess
import typing as t

import pydantic

from src.utils.common import print_cmd
from src.utils.common import PrintCmdCallable


class RsyncConfig(pydantic.BaseModel):
    host: str = ""
    user: str = ""
    module: str = ""
    root: str = ""
    rsh: str = ""  # deprecated
    args: list[str] = []

    def is_complete(self):
        return self.host != ""


class RsyncBaseOptions:
    host: str
    module: t.Optional[str]
    root: str
    args: list[str]

    def __init__(
        self,
        config: RsyncConfig,
    ):
        if not config.is_complete():
            raise Exception("You need to configure rsync.")

        self.host = (config.user + "@" if config.user != "" else "") + config.host
        self.module = config.module if config.module != "" else None
        self.root = config.root

        if self.module is not None and not self.root.startswith("/"):
            self.root = "/" + self.root
        if self.root not in ("", "/") and not self.root.endswith("/"):
            self.root += "/"

        ssh_args = ["-e", config.rsh] if config.rsh != "" else []
        self.args = [*ssh_args, *config.args]

    def path(self):
        prefix = ":" + self.module if self.module is not None else ""
        return f"{self.host}:{prefix}{self.root}"


class RsyncBackupOptions(RsyncBaseOptions):
    def __init__(  # noqa: CFQ002 (max arguments)
        self,
        config: RsyncConfig,
        delete_from_destination: bool,
        compress: bool = True,
        cross_filesystem_boundaries: bool = True,
        verbose: bool = False,
        show_progress: bool = False,
        dry_run: bool = False,
    ):
        super().__init__(config)

        info_args = [
            "-h",
            *(["-v"] if verbose else []),
            *(["--info=progress2"] if show_progress else []),
        ]
        backup_args = [
            *(["--delete"] if delete_from_destination else []),
            # '--mkpath', # --mkpath supported only since 3.2.3
            *(["-z"] if compress else []),
            *(["-n"] if dry_run else []),
        ]
        archive_args = [
            "-a",
            # '-N', # -N (--crtimes) supported only on OS X apparently
            "--numeric-ids",
            *(["-x"] if not cross_filesystem_boundaries else []),
        ]
        self.args.extend([*info_args, *backup_args, *archive_args])


class RsyncListOptions(RsyncBaseOptions):
    def __init__(
        self,
        config: RsyncConfig,
    ):
        super().__init__(config)

        list_args = [
            "--list-only",
        ]
        self.args.extend([*list_args])


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
        *opt.args,
        "--",
        source,
        f"{opt.path()}{destination}",
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
        *opt.args,
        "--backup-dir",
        f"{opt.root}{backup_dir}",
        "--",
        source,
        f"{opt.path()}{destination}",
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
        opt.args.extend(["--link-dest", f"{opt.root}{old_backup_dir}"])
    cmd = [
        "rsync",
        *opt.args,
        "--",
        source,
        f"{opt.path()}{new_backup}",
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
        *opt.args,
        "--",
        f"{opt.path()}{source}",
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
) -> tuple[list[str], list[tuple[str, str]]]:
    """
    :return: Tuple of cmdline and list of date-file-tuples
    """
    opt = RsyncListOptions(config=config)
    cmd = [
        "rsync",
        *opt.args,
        "--",
        f"{opt.path()}{target}",
    ]
    date_file_tuples: list[tuple[str, str]] = []
    if not dry_run:
        print_cmd_callback(cmd, None)
        result = subprocess.run(
            cmd, capture_output=True, encoding="utf-8", universal_newlines=True, check=True
        )
        # Output contains lines like: drwxr-xr-x          4,096 2022/11/07 18:47:30 backup-2022-11-07_18.47
        regex = re.compile("[^ ]+ + [^ ]+ +(?P<date>[^ ]+ +[^ ]+) +(?P<file>.*)")
        for line in result.stdout.split("\n"):
            match = regex.match(line)
            if match and match.group("file") != ".":
                date_file_tuples.append((match.group("date"), match.group("file")))
    return cmd, date_file_tuples
