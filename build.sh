#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    printf 'Usage: %s [merchromio|scribiosa]\n' "$0" >&2
}

build_module() {
    local module="$1"
    "$ROOT_DIR/$module/build.sh"
}

if [[ "$#" -gt 1 ]]; then
    usage
    exit 2
fi

if [[ "$#" -eq 1 ]]; then
    case "$1" in
        merchromio|scribiosa) build_module "$1" ;;
        *) usage; exit 2 ;;
    esac
else
    build_module merchromio
    build_module scribiosa
fi