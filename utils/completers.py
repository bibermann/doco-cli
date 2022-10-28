import os
import typing as t

import typer


class _FileCompleter:
    def __init__(self, param: t.Optional[str], predicate: t.Callable[[str], bool] = lambda _: True):
        self.param = param
        self.predicate = predicate

    def __call__(self, ctx: typer.Context, incomplete: str) -> t.Generator[str, None, None]:
        past_values: t.Optional[t.Union[str, tuple[str]]] = ctx.params.get(
            self.param) if self.param is not None else None

        target_dir = os.path.dirname(incomplete)
        try:
            names = os.listdir(target_dir or ".")
        except OSError:
            return
        incomplete_part = os.path.basename(incomplete)

        for name in names:
            if not name.startswith(incomplete_part):
                continue
            candidate = os.path.join(target_dir, name)
            if type(past_values) is tuple and os.path.abspath(candidate) in map(os.path.abspath, past_values):
                continue
            if not self.predicate(candidate):
                continue
            yield candidate + "/" if os.path.isdir(candidate) else candidate


class PathCompleter(_FileCompleter):
    def __init__(self, param: t.Optional[str] = None):
        _FileCompleter.__init__(self, param=param)


class DirectoryCompleter(_FileCompleter):
    def __init__(self, param: t.Optional[str] = None):
        _FileCompleter.__init__(self, param=param, predicate=os.path.isdir)


class ComposeProjectCompleter(_FileCompleter):
    def __init__(self, param: t.Optional[str] = None):
        _FileCompleter.__init__(
            self,
            param=param,
            predicate=lambda path: \
                os.path.isdir(path) or
                ('docker-compose' in path and (path.endswith('.yml') or path.endswith('.yaml'))),
        )
