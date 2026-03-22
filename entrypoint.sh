#!/bin/sh
set -eu

FLAG_PATH="${FLAG_PATH:-/var/ctf/flag.txt}"

if [ -n "${GZCTF_FLAG:-}" ]; then
    mkdir -p "$(dirname "$FLAG_PATH")"
    printf '%s' "$GZCTF_FLAG" > "$FLAG_PATH"
fi

python ensure_key.py
exec python server.py
