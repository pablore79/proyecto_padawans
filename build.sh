#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE=(
  docker compose
  --project-directory "$REPOSITORY_ROOT"
  -f "$REPOSITORY_ROOT/docker-compose.yml"
)

# Stop the Compose project before rebuilding; `down` keeps named volumes intact.
"${COMPOSE[@]}" down

# With no service arguments, builds both backend and frontend; pass a service name to build only it.
exec "${COMPOSE[@]}" build "$@"
