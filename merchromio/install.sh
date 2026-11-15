#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${MERCHROMIO_IMAGE:-localhost/merchromio:latest}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"

"$MODULE_DIR/build.sh"
mkdir -p "$BIN_DIR"
install -m 0755 "$MODULE_DIR/merchromio" "$BIN_DIR/merchromio"

printf 'Installed merchromio to %s/merchromio (image: %s).\n' "$BIN_DIR" "$IMAGE"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    printf 'Add %s to PATH to run merchromio.\n' "$BIN_DIR"
fi