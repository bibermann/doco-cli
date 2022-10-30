import typing as t

import typer


def project_name_callback(ctx: typer.Context, project_name: t.Optional[str]) -> t.Optional[str]:
    if ctx.resilient_parsing:
        return project_name

    if project_name is not None:
        if project_name.endswith("/"):
            project_name = project_name[:-1]
        if "/" in project_name or project_name == "." or project_name == "":
            raise typer.BadParameter(f"Project name '{project_name}' is invalid.")

    return project_name
