#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if ! [[ "$*" =~ ^(-p|--patch|-m|--minor|--major)$ ]]; then
  echo >&2 "Usage: $0 -p|--patch|-m|--minor|--major"
  exit 1
fi

# build early to catch errors
#*****************************

poetry build

# run bumpver
#*************

get_current_version() {
  eval $(poetry run bumpver show --no-fetch --env)
  echo "$CURRENT_VERSION"
}

OLD_VERSION="$(get_current_version)"

poetry run bumpver update --no-fetch "$@"
CURRENT_VERSION="$(get_current_version)"

# update CHANGELOG.md
#*********************

OLD_HEADER_LINE="## \[Unreleased\]"
NEW_HEADER_LINE="## \[$CURRENT_VERSION\] -- $(date --iso)"
sed -E "s/^$OLD_HEADER_LINE\$/$OLD_HEADER_LINE\n\n$NEW_HEADER_LINE/" -i CHANGELOG.md

OLD_UNRELEASED_LINE="\[Unreleased\]: (.*)\/$OLD_VERSION...HEAD"
NEW_UNRELEASED_LINE="\[Unreleased\]: \1\/$CURRENT_VERSION...HEAD"
NEW_RELEASE_LINE="\[$CURRENT_VERSION\]: \1\/$OLD_VERSION...$CURRENT_VERSION"
sed -E "s/^$OLD_UNRELEASED_LINE\$/$NEW_UNRELEASED_LINE\n$NEW_RELEASE_LINE/" -i CHANGELOG.md

# amend commit, tag and publish
#*******************************

git commit --amend --no-edit -- CHANGELOG.md
git tag -a -m "Release version $CURRENT_VERSION" "v$CURRENT_VERSION"

poetry publish --build
