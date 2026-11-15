#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
    printf 'scribiosa requires uv. Install it from https://docs.astral.sh/uv/ first.\n' >&2
    exit 1
fi

if ! command -v pandoc >/dev/null 2>&1; then
    printf 'scribiosa requires Pandoc on PATH.\n' >&2
    exit 1
fi

exec uv tool install --force "$MODULE_DIR"