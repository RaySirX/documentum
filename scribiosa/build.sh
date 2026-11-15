#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
    printf 'scribiosa build requires uv.\n' >&2
    exit 1
fi

cd "$MODULE_DIR"
exec uv build