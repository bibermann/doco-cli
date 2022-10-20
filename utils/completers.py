import os

import argcomplete


class ComposeProjectCompleter(argcomplete.completers._FilteredFilesCompleter):
    def __init__(self):
        argcomplete.completers._FilteredFilesCompleter.__init__(
            self,
            predicate=lambda path: \
                os.path.isdir(path) or
                ('docker-compose' in path and (path.endswith('.yml') or path.endswith('.yaml')))
        )
