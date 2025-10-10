import json
import os
import pathlib
import subprocess
import typing as t

import yaml

from src.utils.common import print_cmd
from src.utils.common import PrintCmdCallable
from src.utils.common import relative_path_if_below


def load_compose_config(cwd: str, file: str, profiles: list[str]) -> tuple[t.Mapping[str, t.Any], str]:
    cmd = ["docker", "compose", "-f", file]
    for profile in profiles:
        cmd.extend(["--profile", profile])
    cmd.append("config")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        universal_newlines=True,
        check=True,
    )
    return yaml.safe_load(result.stdout), result.stdout


def load_compose_profiles(cwd: str, file: str) -> list[str]:
    result = subprocess.run(
        ["docker", "compose", "-f", file, "config", "--profiles"],
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        universal_newlines=True,
        check=True,
    )
    return result.stdout.splitlines()


def load_compose_ps(cwd: str, file: str, profiles: list[str]) -> list[t.Mapping[str, t.Any]]:
    cmd = ["docker", "compose", "-f", file]
    for profile in profiles:
        cmd.extend(["--profile", profile])
    cmd.extend(["ps", "--format", "json", "--orphans=false"])
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
        universal_newlines=True,
        check=True,
    )
    if len(result.stdout) > 0 and result.stdout[0] == "[":
        # before docker compose v2.21.0
        return json.loads(result.stdout)
    return [json.loads(line) for line in result.stdout.split("\n") if line]


def run_compose(  # noqa: CFQ002 (max arguments)
    project_dir,
    project_file,
    profiles: list[str],
    command: list[str],
    dry_run: bool = False,
    cancelable: bool = False,
    print_cmd_callback: PrintCmdCallable = print_cmd,
):
    cmd = [
        "docker",
        "compose",
        "-f",
        project_file,
    ]
    for profile in profiles:
        cmd.extend(["--profile", profile])
    cmd.extend(command)

    if not dry_run:
        print_cmd_callback(cmd, project_dir)
        try:
            subprocess.run(cmd, cwd=project_dir, check=True)
        except KeyboardInterrupt:
            if not cancelable:
                raise

    return cmd


def find_compose_projects(
    paths: t.Iterable[pathlib.Path], allow_empty: bool
) -> t.Generator[tuple[str, str], None, None]:
    for project in map(str, paths):
        project_dir = None
        project_file = None
        if (
            os.path.isfile(project)
            and "compose" in project
            and (project.endswith(".yml") or project.endswith(".yaml"))
        ):
            project_dir, project_file = os.path.split(project)
            if project_dir == "":
                project_dir = ""
        if project_dir is None or project_file is None:
            for file in ["compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"]:
                if os.path.exists(os.path.join(project, file)):
                    project_dir, project_file = project, file
                    break
        if project_dir is None or project_file is None:
            if allow_empty and os.path.isdir(project):
                project_dir = relative_path_if_below(project)
                yield project_dir, ""
        else:
            project_dir = relative_path_if_below(project_dir)
            yield project_dir, project_file
