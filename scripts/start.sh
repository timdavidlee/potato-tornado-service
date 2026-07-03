#!/usr/bin/env bash
# Build and start the stack (db -> seed -> api).
#
#   scripts/start.sh        # build, then run in the foreground (Ctrl-C to stop)
#   scripts/start.sh -d     # build, then run detached (use scripts/stop.sh to stop)
#
# Requires Docker with BuildKit and an ssh-agent holding your GitHub key — the
# build fetches the private potato-tornado dependency over SSH.
set -euo pipefail

cd "$(dirname "$0")/.."

# Ensure a key is loaded so the SSH-forwarded build can reach GitHub.
if ! ssh-add -l >/dev/null 2>&1; then
    echo "No SSH keys loaded; running ssh-add..." >&2
    ssh-add
fi

docker compose build --ssh default
docker compose up "$@"
