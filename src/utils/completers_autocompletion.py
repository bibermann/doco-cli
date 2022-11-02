"""Completers for legacy autocompletion

This file is needed as long as this bug is not closed:
https://github.com/tiangolo/typer/issues/334

For typer.Argument shell_complete does not work (it does for typer.Option),
so for those we need to use the old functionality of click <8.1.
That's also why we explicitely require click = "8.0.4" in pyproject.toml.

If the bug is fixed, this file can be removed
(usages should be replaced with equivalents in completers.py)
and the explicit click dependency can be removed then.
"""
import os
import typing as t


class _FileCompleter:
    def __init__(self, param: t.Optional[str], predicate: t.Callable[[str], bool] = lambda _: True):
        self.param = param
        self.predicate = predicate

    def __call__(self, incomplete: str) -> list[str]:
        target_dir = os.path.dirname(incomplete)
        try:
            names = os.listdir(target_dir or ".")
        except OSError:
            return []
        incomplete_part = os.path.basename(incomplete)

        candidates = []
        for name in names:
            if not name.startswith(incomplete_part):
                continue
            candidate = os.path.join(target_dir, name)
            if not self.predicate(candidate):
                continue
            candidates.append(candidate + "/" if os.path.isdir(candidate) else candidate)

        return candidates


class LegacyPathCompleter(_FileCompleter):
    def __init__(self, param: t.Optional[str] = None):
        _FileCompleter.__init__(self, param=param)


class LegacyDirectoryCompleter(_FileCompleter):
    def __init__(self, param: t.Optional[str] = None):
        _FileCompleter.__init__(self, param=param, predicate=os.path.isdir)


class LegacyComposeProjectCompleter(_FileCompleter):
    def __init__(self, param: t.Optional[str] = None):
        _FileCompleter.__init__(
            self,
            param=param,
            predicate=lambda path: os.path.isdir(path)
            or ("docker-compose" in path and (path.endswith(".yml") or path.endswith(".yaml"))),
        )
