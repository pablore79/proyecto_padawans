#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
compose_file="$project_root/docker-compose.yml"

exec docker compose \
  --project-directory "$project_root" \
  -f "$compose_file" \
  up -d --build --force-recreate
