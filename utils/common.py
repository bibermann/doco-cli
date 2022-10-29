import os
import typing as t

import dotenv

PrintCmdCallable = t.Callable[[list[str], t.Optional[str]], None]


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


def print_cmd(cmd: list[str], cwd: t.Optional[str]) -> None:
    if cwd:
        print(f"Running {cmd} in {relative_path_if_below(cwd)}")
    else:
        print(f"Running {cmd}")
