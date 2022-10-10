import json
import os
import subprocess
import typing as t

import yaml

from utils.common import relative_path_if_below


def load_compose_config(cwd: str, file: str):
    result = subprocess.run(
        ['docker', 'compose', '-f', file, 'config'],
        cwd=cwd,
        capture_output=True,
        encoding='utf-8',
        universal_newlines=True,
        check=True,
    )
    return yaml.safe_load(result.stdout)


def load_compose_ps(cwd: str, file: str):
    result = subprocess.run(
        ['docker', 'compose', '-f', file, 'ps', '--format', 'json'],
        cwd=cwd,
        capture_output=True,
        encoding='utf-8',
        universal_newlines=True,
        check=True,
    )
    return json.loads(result.stdout)


def run_compose(project_dir, project_file, command: t.List[str], dry_run: bool = False,
                cancelable: bool = False):
    cmd = [
        'docker', 'compose', '-f', project_file,
        *command,
    ]
    if not dry_run:
        print(f"Running {cmd} in {project_dir}")
        try:
            subprocess.run(cmd, cwd=project_dir, check=True)
        except KeyboardInterrupt:
            if not cancelable:
                raise

    return cmd


def find_compose_projects(paths: t.Iterable[str]) -> t.Generator[t.Tuple[str, str], None, None]:
    for project in paths:
        project_dir = None
        project_file = None
        if os.path.isfile(project) and 'docker-compose' in project and (
            project.endswith('.yml') or project.endswith('.yaml')):
            project_dir, project_file = os.path.split(project)
            if project_dir == '':
                project_dir = '.'
        if project_dir is None or project_file is None:
            for file in ['docker-compose.yml', 'docker-compose.yaml']:
                if os.path.exists(os.path.join(project, file)):
                    project_dir, project_file = project, file
                    break
        if project_dir is None or project_file is None:
            continue

        project_dir = relative_path_if_below(project_dir)
        yield project_dir, project_file