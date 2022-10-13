import os

import dotenv


def load_env_file():
    return dotenv.dotenv_values('.env')


def relative_path_if_below(path: str, base: str = os.getcwd()) -> str:
    path = os.path.normpath(path)
    relpath = os.path.relpath(path, base)
    if relpath.startswith('../') or base == '/':
        return os.path.abspath(path)
    else:
        if not relpath == '.' and not relpath.startswith('./') and not relpath.startswith('/'):
            return './' + relpath
        else:
            return relpath
