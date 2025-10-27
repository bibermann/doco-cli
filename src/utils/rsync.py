import re
import subprocess
import typing as t

import pydantic

from src.utils.common import print_cmd
from src.utils.common import PrintCmdCallable


class RsyncFilterRule(pydantic.BaseModel):
    project_pattern: re.Pattern
    path_pattern: re.Pattern
    filter: list[str]


class RsyncConfig(pydantic.BaseModel):
    host: str = ""
    user: str = ""
    module: str = ""
    root: str = ""
    rsh: str = ""  # deprecated
    args: list[str] = []
    filter: list[RsyncFilterRule] = []

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
        *,
        project_for_filter: str,
        path_for_filter: str,
        delete_from_destination: bool,
        show_progress: bool,
        verbose: bool,
        compress: bool = True,
        cross_filesystem_boundaries: bool = True,
        preserve_creation_times: bool = False,  # supported only on OS X apparently
        preserve_acls: bool = False,
        preserve_extended_attributes: bool = True,
        preserve_hard_links: bool = False,
        sparse: bool = False,
        dry_run: bool = False,
    ):
        # pylint: disable=too-many-locals
        super().__init__(config)

        info_args = [
            "-h",
            *(["--info=progress2"] if show_progress else []),
            *(["-v"] if verbose else []),
        ]
        backup_args = [
            *(["--delete"] if delete_from_destination else []),
            # '--mkpath', # --mkpath supported only since 3.2.3
            *(["-z"] if compress else []),
            *(["-n"] if dry_run else []),
        ]
        archive_args = [
            "-a",
            *(["-N"] if preserve_creation_times else []),
            *(["-A"] if preserve_acls else []),
            *(["-X"] if preserve_extended_attributes else []),
            *(["-H"] if preserve_hard_links else []),
            *(["-S"] if sparse else []),
            "--numeric-ids",
            *(["-x"] if not cross_filesystem_boundaries else []),
        ]
        filter_args = []
        for filter_ in [
            filter_
            for filter_ in config.filter
            if filter_.project_pattern.search(project_for_filter)
            and filter_.path_pattern.search(path_for_filter)
        ]:
            for filter_rule in filter_.filter:
                filter_args.extend(["-f", filter_rule])
        self.args.extend([*info_args, *backup_args, *archive_args, *filter_args])


class RsyncListOptions(RsyncBaseOptions):
    def __init__(
        self,
        config: RsyncConfig,
        *,
        show_progress: bool,
        verbose: bool,
    ):
        super().__init__(config)

        info_args = [
            "-h",
            *(["--info=progress2"] if show_progress else []),
            *(["-v"] if verbose else []),
        ]
        list_args = [
            "--list-only",
        ]
        self.args.extend([*info_args, *list_args])


def run_rsync_without_delete(  # noqa: CFQ002 (max arguments)
    config: RsyncConfig,
    source: str,
    destination: str,
    project_for_filter: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(
        config=config,
        project_for_filter=project_for_filter,
        path_for_filter=source,
        delete_from_destination=False,
        show_progress=show_progress,
        verbose=verbose,
    )
    cmd = [
        "rsync",
        *opt.args,
        "--",
        source,
        f"{opt.path()}{destination}",
    ]
    if not dry_run:
        print_cmd_callback(cmd=cmd)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_incremental(  # noqa: CFQ002 (max arguments)
    config: RsyncConfig,
    source: str,
    destination: str,
    backup_dir: str,
    project_for_filter: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(
        config=config,
        project_for_filter=project_for_filter,
        path_for_filter=source,
        delete_from_destination=True,
        show_progress=show_progress,
        verbose=verbose,
    )
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
        print_cmd_callback(cmd=cmd)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_backup_with_hardlinks(  # noqa: CFQ002 (max arguments)
    config: RsyncConfig,
    source: str,
    new_backup: str,
    old_backup_dirs: list[str],
    project_for_filter: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> list[str]:
    opt = RsyncBackupOptions(
        config=config,
        project_for_filter=project_for_filter,
        path_for_filter=source,
        delete_from_destination=True,
        show_progress=show_progress,
        verbose=verbose,
    )
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
        print_cmd_callback(cmd=cmd)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_download_incremental(  # noqa: CFQ002 (max arguments)
    config: RsyncConfig,
    source: str,
    destination: str,
    project_for_filter: str,
    show_progress: bool,
    verbose: bool,
    delete_from_destination: bool = True,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
    extra_args: t.Union[list[str], None] = None,
) -> list[str]:
    opt = RsyncBackupOptions(
        config=config,
        project_for_filter=project_for_filter,
        path_for_filter=destination,
        delete_from_destination=delete_from_destination,
        show_progress=show_progress,
        verbose=verbose,
    )
    cmd = [
        "rsync",
        *opt.args,
        *(extra_args or []),
        "--",
        f"{opt.path()}{source}",
        destination,
    ]
    if not dry_run:
        print_cmd_callback(cmd=cmd)
        subprocess.run(cmd, check=True)
    return cmd


def run_rsync_list(
    config: RsyncConfig,
    target: str,
    show_progress: bool,
    verbose: bool,
    dry_run: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
) -> tuple[list[str], list[tuple[str, str]]]:
    """
    :return: Tuple of cmdline and list of date-file-tuples
    """
    opt = RsyncListOptions(config=config, show_progress=show_progress, verbose=verbose)
    cmd = [
        "rsync",
        *opt.args,
        "--",
        f"{opt.path()}{target}",
    ]
    date_file_tuples: list[tuple[str, str]] = []
    if not dry_run:
        print_cmd_callback(cmd=cmd)
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
