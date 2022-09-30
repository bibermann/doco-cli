import argparse
import dataclasses
import os
import re
import subprocess
import typing as t

import rich
import rich.box
import rich.markup
import rich.table
import rich.tree

from utils.common import find_compose_projects
from utils.common import load_compose_config
from utils.common import load_compose_ps
from utils.common import relative_path_if_below


def create_table(alternate_bg: bool) -> rich.table.Table:
    return rich.table.Table(
        title_justify='left',
        style='dim',
        header_style='i',
        box=rich.box.SQUARE,
        row_styles=['on grey7', ''] if alternate_bg else None,
    )


def colored_container_state(state: str) -> str:
    if state == 'running':
        return f'[b green]{state}[/]'
    elif state == 'exited' or state == 'dead':
        return f'[b red]{state}[/]'
    else:
        return f'[b yellow]{state}[/]'


def dim_path(path: str, dimmed_prefix: str, bold: bool = False) -> str:
    if path.startswith(dimmed_prefix):
        return f"[dim]{dimmed_prefix}[/]{'[b]' if bold else ''}{path[len(dimmed_prefix):]}{'[/]' if bold else ''}"
    else:
        return f"{'[b]' if bold else ''}{path}{'[/]' if bold else ''}"


def colored_path(path: str, dimmed_prefix: t.Optional[str] = None) -> str:
    formatted = re.sub(r'^/disk/([^/]+)/volumes/([^/]+)(.*)$',
                       r'[dim]/disk/[/][b]\1[/][dim]/volumes/[/][b]\2[/]\3', path)
    if formatted != path:
        return formatted
    return dim_path(path, dimmed_prefix=dimmed_prefix,
                    bold=True) if dimmed_prefix is not None else f"[b]{path}[/]"


def colored_readonly(text: str, ro: bool, is_bind_mount: bool) -> str:
    ro_text = text if ro else f'[dark_orange]{text}[/]'
    return ro_text if is_bind_mount else f'[dim]{ro_text}[/]'


def colored_image(image: str) -> str:
    if not ':' in image:
        image += ':latest'
    return re.sub(r'^(docker.io/)?([^:]*):(.*)', r'[bright_blue][dim]\1[/][b]\2[/][dim]:[/]\3[/]', image)


def colored_dockerfile(dockerfile: str, dimmed_prefix: str) -> str:
    formatted = dim_path(dockerfile, dimmed_prefix=dimmed_prefix)
    formatted = re.sub(r'^(.*)Dockerfile(.*)$',
                       r'[bright_blue]\1[dim]Dockerfile[/]\2[/]', formatted)
    if formatted != dockerfile:
        return formatted
    return f'[bright_blue]{dockerfile}[/]'


def colored_key_value(text: str, key: str, value: str) -> str:
    if value.lower() in ['true', 'yes', 'on']:
        return f"[green]{text}[/]"
    elif value.lower() in ['false', 'no', 'off']:
        return f"[red]{text}[/]"
    elif value.isnumeric():
        return f"[bright_blue]{text}[/]"
    elif re.search(r'(?:\b|_)(?:pw|pass|password|token|secret)(?:\b|_)', key.lower()):
        return f"[dim dark_orange]{text}[/]"
    else:
        return text.replace(',', '[b white],[/]')


def colored_port_mapping(mapping: t.Tuple[str, str]) -> str:
    return f'{mapping[0]}[dim]:{mapping[1]}[/]'


@dataclasses.dataclass
class PrintOptions:
    print_path: bool
    output_build: bool
    list_environment: bool
    list_volumes: int

    align_right: bool
    alternate_rows: bool


def print_project(compose_dir: str, compose_file: str, options: PrintOptions):
    try:
        compose_config = load_compose_config(compose_dir, compose_file)
    except subprocess.CalledProcessError as e:
        tree = rich.tree.Tree(f"[b]{rich.markup.escape(os.path.join(compose_dir, compose_file))}")
        tree.add(f'[red]{rich.markup.escape(e.stderr.strip())}')
        rich.print(tree)
        return

    justify: rich.console.JustifyMethod = 'left'
    if options.align_right: justify = 'right'

    compose_ps = load_compose_ps(compose_dir, compose_file)

    compose_id = f"[b]{rich.markup.escape(compose_config['name'])}[/]"
    if options.print_path:
        compose_id += f" [dim]{rich.markup.escape(os.path.join(compose_dir, compose_file))}[/]"
    tree = rich.tree.Tree(compose_id)
    for service_name, service in compose_config['services'].items():
        state = next((s['State'] for s in compose_ps if s['Service'] == service_name), 'exited')
        is_image = 'image' in service
        dockerfile_path = None
        if not is_image:
            dockerfile_path = relative_path_if_below(
                os.path.join(service['build']['context'],
                             service['build']['dockerfile'])
            )
        source = colored_image(rich.markup.escape(service['image'])) if is_image \
            else colored_dockerfile(rich.markup.escape(dockerfile_path), rich.markup.escape(compose_dir))

        ports = ''
        if 'ports' in service:
            ports = ' '.join(colored_port_mapping((p['published'], p['target'])) for p in service['ports'])

        service_line = [
            colored_container_state(state),
            f"[b]{rich.markup.escape(service_name)}[/]",
            ports,
            source,
        ]
        s = tree.add(' '.join(z for z in service_line if z != ''))

        if options.output_build and not is_image:
            build_context = dim_path(rich.markup.escape(relative_path_if_below(service['build']['context'])),
                                     dimmed_prefix=rich.markup.escape(compose_dir))
            s.add(f'[i]Build context:[/] {build_context}')

        if options.output_build and not is_image and 'args' in service['build']:
            table = create_table(alternate_bg=options.alternate_rows and justify == 'left')
            s.add(table)
            table.add_column("Build argument", no_wrap=True, justify=justify)
            table.add_column("Value")
            for arg, value in service['build']['args'].items():
                table.add_row(
                    colored_key_value(rich.markup.escape(arg), key=arg, value=value)
                    if value != '' else f'[dim]{rich.markup.escape(arg)}[/]',
                    colored_key_value(rich.markup.escape(value), key=arg, value=value))

        if options.list_environment and 'environment' in service:
            table = create_table(alternate_bg=options.alternate_rows and justify == 'left')
            s.add(table)
            table.add_column("Environment variable", no_wrap=True, justify=justify)
            table.add_column("Value")
            for env, value in service['environment'].items():
                table.add_row(
                    colored_key_value(rich.markup.escape(env), key=env, value=value)
                    if value != '' else f'[dim]{rich.markup.escape(env)}[/]',
                    colored_key_value(rich.markup.escape(value), key=env, value=value))

        if options.list_volumes >= 1 and 'volumes' in service:
            table = create_table(alternate_bg=options.alternate_rows)
            s.add(table)
            table.add_column("Volume")
            table.add_column("Container path")
            table.add_column("ro/rw")
            for volume in service['volumes']:
                ro = volume.get('read_only', False)
                is_volume_mount = volume['type'] == 'volume'
                is_bind_mount = volume['type'] == 'bind'
                if is_volume_mount:
                    source_volume = rich.markup.escape(volume['source'])
                elif is_bind_mount:
                    source_volume = colored_path(rich.markup.escape(relative_path_if_below(volume['source'])),
                                                 dimmed_prefix=rich.markup.escape(compose_dir))
                else:
                    source_volume = f"{rich.markup.escape(volume['source'])} [dim]({volume['type']})[/]"
                files = rich.tree.Tree(colored_readonly(rich.markup.escape(source_volume), ro, is_bind_mount))
                if options.list_volumes >= 2 and volume['source'].startswith('/') and os.path.isdir(
                    volume['source']):
                    try:
                        for f in sorted(os.listdir(volume['source'])):
                            if os.path.isdir(os.path.join(volume['source'], f)):
                                files.add(f"[yellow]{rich.markup.escape(f)}/[/]")
                            else:
                                files.add(rich.markup.escape(f))
                    except PermissionError:
                        pass
                table.add_row(files,
                              colored_readonly(rich.markup.escape(volume['target']), ro, is_bind_mount),
                              colored_readonly('ro' if ro else 'rw', ro, is_bind_mount))

    rich.print(tree)


def add_to_parser(parser: argparse.ArgumentParser):
    group = parser.add_argument_group(title='details')
    group.add_argument('-p', '--path', action='store_true', help='print path of compose file')
    group.add_argument('-b', '--build', action='store_true', help='output build context and arguments')
    group.add_argument('-e', '--envs', action='store_true', help='list environment variables')
    group.add_argument('-v', '--volumes', action='count', default=0,
                       help='list volumes (use -vv to also list content)')
    group.add_argument('-a', '--all', action='count', default=0, help='like -pbev (use -aa for -pbevv)')
    group = parser.add_argument_group(title='formatting')
    group.add_argument('-r', '--align-right', action='store_true', help='right-align variable names')
    group.add_argument('--alternate-rows', action='store_true', help='alternate row colors in tables')


def main(args) -> int:
    for compose_dir, compose_file in find_compose_projects(args.projects):
        print_project(
            compose_dir=compose_dir,
            compose_file=compose_file,
            options=PrintOptions(
                print_path=args.all >= 1 or args.path,
                output_build=args.all >= 1 or args.build,
                list_environment=args.all >= 1 or args.envs,
                list_volumes=max(args.all, args.volumes),
                align_right=args.align_right,
                alternate_rows=args.alternate_rows,
            )
        )

    return 0
