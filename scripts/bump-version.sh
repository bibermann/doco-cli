#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

eval $(poetry run bumpver show --no-fetch --env)
OLD_VERSION="$CURRENT_VERSION"

poetry run bumpver update --no-fetch "$@"

eval $(poetry run bumpver show --no-fetch --env)

OLD_HEADER_LINE="## \[Unreleased\]"
NEW_HEADER_LINE="## \[$CURRENT_VERSION\] -- $(date --iso)"
sed -E "s/^$OLD_HEADER_LINE\$/$OLD_HEADER_LINE\n\n$NEW_HEADER_LINE/" -i CHANGELOG.md

OLD_UNRELEASED_LINE="\[Unreleased\]: (.*)\/$OLD_VERSION...HEAD"
NEW_UNRELEASED_LINE="\[Unreleased\]: \1\/$CURRENT_VERSION...HEAD"
NEW_RELEASE_LINE="\[$CURRENT_VERSION\]: \1\/$OLD_VERSION...$CURRENT_VERSION"
sed -E "s/^$OLD_UNRELEASED_LINE\$/$NEW_UNRELEASED_LINE\n$NEW_RELEASE_LINE/" -i CHANGELOG.md

git commit --amend --no-edit -- CHANGELOG.md

git tag -a -m "$CURRENT_VERSION" "$CURRENT_VERSION"
