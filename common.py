import json
import os
import subprocess
import typing as t

import dotenv
import yaml


def load_env_file():
    return dotenv.dotenv_values('.env')


def load_compose_config(cwd: str, file: str):
    result = subprocess.run(
        ['docker', 'compose', '-f', file, 'config'],
        # env={
        #    'PATH': os.getenv('PATH'),
        # },
        capture_output=True,
        encoding='utf-8',
        universal_newlines=True,
        cwd=cwd,
    )
    result.check_returncode()
    return yaml.safe_load(result.stdout)


def load_compose_ps(cwd: str, file: str):
    result = subprocess.run(
        ['docker', 'compose', '-f', file, 'ps', '--format', 'json'],
        # env={
        #    'PATH': os.getenv('PATH'),
        # },
        capture_output=True,
        encoding='utf-8',
        universal_newlines=True,
        cwd=cwd,
    )
    result.check_returncode()
    return json.loads(result.stdout)


def relative_path_if_below(path: str) -> str:
    is_dir = os.path.isdir(path)
    relpath = os.path.relpath(path)
    if relpath.startswith('../') or os.getcwd() == '/':
        return os.path.abspath(path) + ('/' if is_dir else '')
    else:
        if not relpath == '.' and not relpath.startswith('./') and not relpath.startswith('/'):
            return './' + relpath + ('/' if is_dir and relpath != '' else '')
        else:
            return relpath


def find_compose_projects(paths: t.Iterable[str]) -> t.Generator[None, t.Tuple[str, str], None]:
    for project in paths:
        compose_dir = None
        compose_file = None
        if os.path.isfile(project) and 'docker-compose' in project and (
            project.endswith('.yml') or project.endswith('.yaml')):
            compose_dir, compose_file = os.path.split(project)
            if compose_dir == '':
                compose_dir = '.'
        if compose_dir is None or compose_file is None:
            for file in ['docker-compose.yml', 'docker-compose.yaml']:
                if os.path.exists(os.path.join(project, file)):
                    compose_dir, compose_file = project, file
                    break
        if compose_dir is None or compose_file is None:
            continue

        compose_dir = relative_path_if_below(compose_dir)
        yield compose_dir, compose_file
