import typing as t

import typer


def project_id_callback(ctx: typer.Context, project_id: t.Optional[str]) -> t.Optional[str]:
    if ctx.resilient_parsing:
        return project_id

    if project_id is not None:
        if project_id.endswith('/'):
            project_id = project_id[:-1]
        if '/' in project_id or project_id == '.' or project_id == '':
            raise typer.BadParameter(f"Project name '{project_id}' is invalid.")

    return project_id
