#!/usr/bin/env bash
# Stop the stack and remove its containers.
#
#   scripts/stop.sh         # stop containers, keep the seeded Postgres volume
#   scripts/stop.sh -v      # also delete the pgdata volume (next start re-seeds)
#
# Any extra args are passed through to `docker compose down`.
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose down "$@"
