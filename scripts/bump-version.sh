#!/usr/bin/env bash
set -euo pipefail

poetry run bumpver update --no-fetch "$@"
eval $(poetry run bumpver show --no-fetch --env)
git tag -a -m "$CURRENT_VERSION" "$CURRENT_VERSION"
