#!/usr/bin/env bash
set -euo pipefail

REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

exec docker compose \
  --project-directory "$REPOSITORY_ROOT" \
  -f "$REPOSITORY_ROOT/docker-compose.yml" \
  build "$@"
