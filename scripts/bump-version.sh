#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <major|minor|patch|stable|alpha|beta|rc|post|dev>" >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INIT_FILE="$REPO_ROOT/src/shablon/__init__.py"

NEW_VERSION="$(uv version --bump "$1" --short)"

sed -i '' -E "s/^__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" "$INIT_FILE"

echo "Bumped to $NEW_VERSION"
