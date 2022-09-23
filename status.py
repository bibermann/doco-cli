#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import typing as t

import dotenv
import rich
import rich.table
import rich.tree
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


def colored_container_state(state: str):
    if state == 'running':
        return f'[b green]{state}[/]'
    elif state == 'exited' or state == 'dead':
        return f'[b red]{state}[/]'
    else:
        return f'[b yellow]{state}[/]'


def colored_path(path: str):
    formatted = re.sub(r'^/disk/([^/]+)/volumes/([^/]+)(.*)$',
                       r'[dim]/disk/[/][b]\1[/][dim]/volumes/[/][b]\2[/]\3', path)
    if formatted != path:
        return formatted
    return f'[b]{path}[/]'


def colored_readonly(text: str, ro: bool, is_volume: bool):
    ro_text = text if ro else f'[dark_orange]{text}[/]'
    return ro_text if not is_volume else f'[dim]{ro_text}[/]'


def colored_image(image: str):
    if not ':' in image:
        image += ':latest'
    return re.sub(r'^(docker.io/)?([^:]*):(.*)', r'[bright_blue][dim]\1[/][b]\2[/][dim]:[/]\3[/]', image)


def dim_path(path: str, dimmed_prefix: str):
    if path.startswith(dimmed_prefix):
        return f'[dim]{dimmed_prefix}[/]{path[len(dimmed_prefix):]}'
    else:
        return path


def colored_dockerfile(dockerfile: str, dimmed_prefix: str):
    formatted = dim_path(dockerfile, dimmed_prefix)
    formatted = re.sub(r'^(.*)Dockerfile(.*)$',
                       r'[bright_blue]\1[dim]Dockerfile[/]\2[/]', formatted)
    if formatted != dockerfile:
        return formatted
    return f'[bright_blue]{dockerfile}[/]'


def relative_path_if_below(path: str):
    relpath = os.path.relpath(path)
    if relpath.startswith('../'):
        return os.path.abspath(path)
    else:
        if not relpath == '.' and not relpath.startswith('./') and not relpath.startswith('/'):
            return './' + relpath
        else:
            return relpath


def colored_port_mapping(mapping: t.Tuple[str, str]):
    return f'{mapping[0]}[dim]:{mapping[1]}[/]'


def print_project(project: str, print_path: bool, output_build: bool, list_volumes: int,
                  list_environment: bool):
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
        return

    compose_dir = relative_path_if_below(compose_dir)

    try:
        compose_config = load_compose_config(compose_dir, compose_file)
    except subprocess.CalledProcessError as e:
        tree = rich.tree.Tree(f"[b]{os.path.join(compose_dir, compose_file)}")
        tree.add(f'[red]{e.stderr.strip()}')
        rich.print(tree)
        return

    compose_ps = load_compose_ps(compose_dir, compose_file)

    compose_id = f"[b]{compose_config['name']}[/]"
    if print_path:
        compose_id += f" [dim]{os.path.join(compose_dir, compose_file)}[/]"
    tree = rich.tree.Tree(compose_id)
    for service_name, service in compose_config['services'].items():
        # print(json.dumps(service, indent=4))
        state = next((s['State'] for s in compose_ps if s['Service'] == service_name), 'exited')
        is_image = 'image' in service
        dockerfile_path = None
        if not is_image:
            dockerfile_path = relative_path_if_below(
                os.path.join(service['build']['context'],
                             service['build']['dockerfile'])
            )
        source = colored_image(service['image']) if is_image \
            else colored_dockerfile(dockerfile_path, compose_dir)

        ports = ''
        if 'ports' in service:
            ports = ' '.join(colored_port_mapping((p['published'], p['target'])) for p in service['ports'])

        s = tree.add(
            f"[b]{service_name}[/] {ports + ' ' if ports != '' else ''}{colored_container_state(state)} {source}")

        if output_build and not is_image:
            build_context = dim_path(relative_path_if_below(service['build']['context']), compose_dir)
            s.add(f'[i]Build context:[/] {build_context}')

        if list_volumes > 0 and 'volumes' in service:
            table = rich.table.Table(title_justify='left', style='dim', header_style='i')
            s.add(table)
            table.add_column("Volume")
            table.add_column("Container path")
            table.add_column("ro/rw")
            for volume in service['volumes']:
                ro = volume.get('read_only', False)
                is_volume = volume['type'] == 'volume'
                source_volume = volume['source'] if is_volume else \
                    colored_path(relative_path_if_below(volume['source']))
                files = rich.tree.Tree(colored_readonly(colored_path(source_volume), ro, is_volume))
                if list_volumes > 1 and volume['source'].startswith('/') and os.path.isdir(volume['source']):
                    for f in sorted(os.listdir(volume['source'])):
                        if os.path.isdir(os.path.join(volume['source'], f)):
                            files.add(f"[yellow]{f}/[/]")
                        else:
                            files.add(f)
                table.add_row(files,
                              colored_readonly(volume['target'], ro, is_volume),
                              colored_readonly('ro' if ro else 'rw', ro, is_volume))

        if output_build and not is_image and 'args' in service['build']:
            table = rich.table.Table(title_justify='left', style='dim', header_style='i')
            s.add(table)
            table.add_column("Build argument")
            table.add_column("Value")
            for arg, value in service['build']['args'].items():
                table.add_row(arg if value != '' else f'[dim]{arg}[/]', value)

        if list_environment and 'environment' in service:
            table = rich.table.Table(title_justify='left', style='dim', header_style='i')
            s.add(table)
            table.add_column("Environment variable")
            table.add_column("Value")
            for env, value in service['environment'].items():
                table.add_row(env if value != '' else f'[dim]{env}[/]', value)

    rich.print(tree)


def main() -> int:
    parser = argparse.ArgumentParser(prog='PROG')
    parser.add_argument('projects', nargs='*', default=['.'],
                        help='compose files and/or directories containing a docker-compose.y[a]ml')
    parser.add_argument('-v', '--volumes', action='count', default=0, help='list volumes')
    parser.add_argument('-e', '--envs', action='store_true', help='list environment variables')
    parser.add_argument('-b', '--build', action='store_true', help='output build context and arguments')
    parser.add_argument('-p', '--path', action='store_true', help='print path of compose file')
    args = parser.parse_args()

    for project in args.projects:
        print_project(project,
                      print_path=args.path,
                      output_build=args.build,
                      list_volumes=args.volumes,
                      list_environment=args.envs,
                      )

    return 0


if __name__ == '__main__':
    sys.exit(main())
