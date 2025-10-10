#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

poetry run typer src.main utils docs --name doco --title Doco --output docs/doco-help.md
