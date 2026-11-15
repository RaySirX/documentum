#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${MERCHROMIO_IMAGE:-localhost/merchromio:latest}"

if command -v podman >/dev/null 2>&1; then
    CONTAINER_ENGINE=(podman)
elif command -v docker >/dev/null 2>&1; then
    CONTAINER_ENGINE=(docker)
elif command -v flatpak-spawn >/dev/null 2>&1; then
    CONTAINER_ENGINE=(flatpak-spawn --host podman)
else
    printf 'merchromio requires Podman or Docker.\n' >&2
    exit 1
fi

exec "${CONTAINER_ENGINE[@]}" build --tag "$IMAGE" "$MODULE_DIR"