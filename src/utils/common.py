import dataclasses
import os
import typing as t

import dotenv


@dataclasses.dataclass
class PrintCmdData:
    cmd: t.Optional[list[str]] = None
    cwd: t.Optional[str] = None
    create_dir: t.Optional[str] = None


class PrintCmdCallable(t.Protocol):
    def __call__(self, cmd: list[str], cwd: t.Optional[str] = ..., conditional: bool = ...) -> None:
        ...


def load_env_file():
    return dotenv.dotenv_values(".env")


def dir_from_path(path: str) -> str:
    if path.startswith("/"):
        path = path[1:]
    result = path.replace("/", "__")
    return result


def relative_path(path: str) -> str:
    path = os.path.normpath(path)
    if path.startswith("../") or path.startswith("/"):
        raise ValueError(f"Path '{path}' must be relative and not go upwards.")
    if not path == "." and not path.startswith("./"):
        return "./" + path
    return path


def relative_path_if_below(path: str, base: str = os.getcwd()) -> str:
    path = os.path.normpath(path)
    relpath = os.path.relpath(path, base)
    if relpath.startswith("../") or base == "/":
        return os.path.abspath(path)
    if not relpath == "." and not relpath.startswith("./") and not relpath.startswith("/"):
        return "./" + relpath
    return relpath


def print_cmd(cmd: list[str], cwd: t.Optional[str] = None, conditional: bool = False) -> None:
    verb = "Running" if not conditional else "Would run"
    if cwd:
        print(f"{verb} {cmd} in {relative_path_if_below(cwd)}")
    else:
        print(f"{verb} {cmd}")
