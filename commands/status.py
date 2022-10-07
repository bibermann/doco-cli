import argparse
import dataclasses
import os
import re
import typing as t

import rich
import rich.box
import rich.markup
import rich.table
import rich.tree

from utils.common import relative_path_if_below
from utils.rich import ComposeProject
from utils.rich import Formatted
from utils.rich import get_compose_projects


def create_table(alternate_bg: bool) -> rich.table.Table:
    return rich.table.Table(
        title_justify='left',
        style='dim',
        header_style='i',
        box=rich.box.SQUARE,
        row_styles=['on grey7', ''] if alternate_bg else None,
    )


def colored_container_state(state: str) -> Formatted:
    if state == 'running':
        return Formatted(f'[b green]{Formatted(state)}[/]', True)
    elif state == 'exited' or state == 'dead':
        return Formatted(f'[b red]{Formatted(state)}[/]', True)
    else:
        return Formatted(f'[b yellow]{Formatted(state)}[/]', True)


def dim_path(path: str, dimmed_prefix: str, bold: bool = False) -> Formatted:
    if path.startswith(dimmed_prefix):
        return Formatted(
            f"[dim]{Formatted(dimmed_prefix)}[/]{'[b]' if bold else ''}"
            f"{Formatted(path[len(dimmed_prefix):])}"
            f"{'[/]' if bold else ''}",
            True)
    else:
        return Formatted(
            f"{'[b]' if bold else ''}"
            f"{Formatted(path)}"
            f"{'[/]' if bold else ''}",
            True)


def colored_path(path: str, dimmed_prefix: t.Optional[str] = None) -> Formatted:
    formatted = re.sub(r'^/disk/([^/]+)/volumes/([^/]+)(.*)$',
                       r'[dim]/disk/[/][b]\1[/][dim]/volumes/[/][b]\2[/]\3', path)
    if formatted != path:
        return Formatted(formatted, True)
    return dim_path(path, dimmed_prefix=dimmed_prefix, bold=True) \
        if dimmed_prefix is not None else Formatted(f"[b]{Formatted(path)}[/]", True)


def colored_readonly(text: t.Union[str, Formatted], ro: bool, is_bind_mount: bool) -> Formatted:
    text = Formatted(text)
    ro_text = text if ro else Formatted(f'[dark_orange]{text}[/]', True)
    return ro_text if is_bind_mount else Formatted(f'[dim]{ro_text}[/]', True)


def colored_image(image: str) -> Formatted:
    if not ':' in image:
        image += ':latest'
    return Formatted(
        re.sub(r'^(docker.io/)?([^:]*):(.*)', r'[bright_blue][dim]\1[/][b]\2[/][dim]:[/]\3[/]',
               str(Formatted(image))),
        True)


def colored_dockerfile(dockerfile: str, dimmed_prefix: str) -> Formatted:
    formatted = str(dim_path(dockerfile, dimmed_prefix=dimmed_prefix))
    formatted = re.sub(r'^(.*)Dockerfile(.*)$',
                       r'[bright_blue]\1[dim]Dockerfile[/]\2[/]',
                       formatted)
    if formatted != dockerfile:
        return Formatted(formatted, True)
    return Formatted(f'[bright_blue]{Formatted(dockerfile)}[/]', True)


def colored_key_value(text: t.Union[str, Formatted], key: str, value: str) -> Formatted:
    text = str(Formatted(text))
    if text[-1:] == '\n': text = text[:-1]
    if value.lower() in ['true', 'yes', 'on']:
        return Formatted(f"[green]{text}[/]", True)
    elif value.lower() in ['false', 'no', 'off']:
        return Formatted(f"[red]{text}[/]", True)
    elif value.isnumeric():
        return Formatted(f"[bright_blue]{text}[/]", True)
    elif re.search(r'(?:\b|_)(?:pw|pass|password|token|secret)(?:\b|_)', key.lower()):
        return Formatted(f"[dim dark_orange]{text}[/]", True)
    else:
        return Formatted(text.replace(',', '[b white],[/]'), True)


def colored_port_mapping(mapping: t.Tuple[str, str]) -> Formatted:
    return Formatted(f'{mapping[0]}[dim]:{mapping[1]}[/]', True)


@dataclasses.dataclass
class PrintOptions:
    print_path: bool
    output_build: bool
    list_environment: bool
    list_volumes: int

    align_right: bool
    alternate_rows: bool


def print_project(project: ComposeProject, options: PrintOptions):
    justify: rich.console.JustifyMethod = 'left'
    if options.align_right: justify = 'right'

    compose_id = f"[b]{Formatted(project.config['name'])}[/]"
    if options.print_path:
        compose_id += f" [dim]{Formatted(os.path.join(project.dir, project.file))}[/]"
    compose_id = Formatted(compose_id, True)
    tree = rich.tree.Tree(str(compose_id))

    for service_name, service in project.config['services'].items():
        state = next((s['State'] for s in project.ps if s['Service'] == service_name), 'exited')
        is_image = 'image' in service
        dockerfile_path = None
        if not is_image:
            dockerfile_path = relative_path_if_below(
                os.path.join(service['build']['context'],
                             service['build']['dockerfile'])
            )
        source = colored_image(service['image']) if is_image \
            else colored_dockerfile(dockerfile_path, project.dir + '/')

        ports = ''
        if 'ports' in service:
            ports = Formatted(
                ' '.join(str(colored_port_mapping((p['published'], p['target']))) for p in service['ports']),
                True)

        service_line = [
            str(colored_container_state(state)),
            f"[b]{Formatted(service_name)}[/]",
            str(ports),
            str(source),
        ]
        s = tree.add(' '.join(z for z in service_line if z != ''))

        if options.output_build and not is_image:
            build_context = dim_path(
                relative_path_if_below(service['build']['context']) + '/',
                dimmed_prefix=project.dir + '/')
            s.add(f'[i]Build context:[/] {build_context}')

        if options.output_build and not is_image and 'args' in service['build']:
            table = create_table(alternate_bg=options.alternate_rows and justify == 'left')
            s.add(table)
            table.add_column("Build argument", no_wrap=True, justify=justify)
            table.add_column("Value")
            for arg, value in service['build']['args'].items():
                table.add_row(
                    str(colored_key_value(arg, key=arg, value=value))
                    if value != '' else f'[dim]{Formatted(arg)}[/]',
                    str(colored_key_value(value, key=arg, value=value)))

        if options.list_environment and 'environment' in service:
            table = create_table(alternate_bg=options.alternate_rows and justify == 'left')
            s.add(table)
            table.add_column("Environment variable", no_wrap=True, justify=justify)
            table.add_column("Value")
            for env, value in service['environment'].items():
                table.add_row(
                    str(colored_key_value(env, key=env, value=value))
                    if value != '' else f'[dim]{Formatted(env)}[/]',
                    str(colored_key_value(value, key=env, value=value)))

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
                is_dir = False
                if is_volume_mount:
                    source_volume = Formatted(volume['source'])
                elif is_bind_mount:
                    is_dir = os.path.isdir(volume['source'])
                    source_volume = colored_path(
                        relative_path_if_below(volume['source']) + ('/' if is_dir else ''),
                        dimmed_prefix=project.dir)
                else:
                    source_volume = Formatted(
                        f"{Formatted(volume['source'])} [dim]({Formatted(volume['type'])})[/]", True)
                files = rich.tree.Tree(str(colored_readonly(source_volume, ro, is_bind_mount)))
                if options.list_volumes >= 2 and volume['source'].startswith('/') and os.path.isdir(
                    volume['source']):
                    try:
                        for f in sorted(os.listdir(volume['source'])):
                            if os.path.isdir(os.path.join(volume['source'], f)):
                                files.add(f"[yellow]{Formatted(f)}/[/]")
                            else:
                                files.add(str(Formatted(f)))
                    except PermissionError:
                        pass
                table.add_row(files,
                              str(colored_readonly(volume['target'] + ('/' if is_dir else ''), ro,
                                                   is_bind_mount)),
                              str(colored_readonly('ro' if ro else 'rw', ro, is_bind_mount)))

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
    for project in get_compose_projects(args.projects):
        print_project(
            project=project,
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
