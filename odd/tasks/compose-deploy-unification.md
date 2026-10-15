# Compose and Deploy Unification

## Objective
Use one root `docker-compose.yml` and one root `deploy.sh` to build and deploy the backend/frontend monorepo consistently.

## Problem and Why
The repository has a monorepo Compose configuration alongside a stale production Compose file and an obsolete root Dockerfile. Deployment instructions still point at the old single-service layout, making it unclear which artifacts are authoritative.

## Scope and Constraints
- Keep `backend/Dockerfile` and `frontend/Dockerfile` as the service build definitions.
- Keep one root Compose file, named `docker-compose.yml`, orchestrating PostgreSQL, backend, frontend, and any existing Adminer service.
- Add a root `deploy.sh` that uses that canonical Compose file.
- Update `DEPLOY.md` to use the canonical configuration and commands.
- Remove only the superseded root `Dockerfile` and `docker-compose.prod.yml`.
- Preserve the pre-existing untracked `microservicios_padawans.md` without modification.
- Do not change database volumes/data or deploy containers as part of this repository change.

## Delivery Strategy
- Strategy: ask-on-risk (default); forecast is under the ~400 authored-line budget.
- Route: delegated direct implementation; task spans multiple operational/documentation files and needs preparation while writing.
- Trigger evidence: two Docker definitions are being consolidated, a new script is added, and deployment guidance must be reconciled.

## Tasks
- [x] U1 — Consolidate deployment configuration into root Compose and deploy script; remove obsolete root Dockerfile and production Compose file.
- [x] U2 — Update deployment guidance to describe the canonical monorepo workflow and relevant environment requirements.
- [x] U3 — Validate Compose configuration and shell script; review resulting diff; create a Conventional Commit work unit on the current feature branch; record RDD delivery status.

## Acceptance Criteria
- `docker-compose.yml` is the sole Compose YAML configuration in the repository root.
- The Compose file builds the backend and frontend using their respective Dockerfiles and retains required service dependencies/health checks.
- `deploy.sh` deploys through root `docker compose` without deleting persistent volumes.
- Deployment guidance does not refer to removed production-compose or root-Dockerfile artifacts for the monorepo deployment path.
- Compose configuration parses, script passes shell syntax validation, and the working change is committed with a Conventional Commit message.

## Checks
- `docker compose -f docker-compose.yml config` (if Docker Compose is available; report any missing environment inputs without exposing secrets).
- `bash -n deploy.sh`.
- Inspect `git diff --check`, targeted file references, and final `git status`.

## Progress and Evidence
- Inventory found `docker-compose.yml` already builds `backend/` and `frontend/` independently, with PostgreSQL and Adminer.
- The root `Dockerfile` is an obsolete single-app image definition; `docker-compose.prod.yml` also targets the former single `app` service.
- Receipt-driven development was on (global default/decision) at task start; the review lifecycle was not yet started.
- Implemented U1 and U2: root `docker-compose.yml` remains canonical; added `deploy.sh`; removed the obsolete root `Dockerfile` and `docker-compose.prod.yml`; updated `DEPLOY.md` for the monorepo workflow.
- Checks: `bash -n deploy.sh` exited 0; `docker compose -f docker-compose.yml config --quiet` exited 0; `git diff --check` exited 0. The Compose validation initially warned that the obsolete `version` attribute was ignored, so that attribute was removed and the validation was rerun successfully.
- Scoped diff inspected: changes are limited to the authorized deployment files and the task document. Pre-existing untracked `microservicios_padawans.md` remains untouched.
- Parent spot checks: Compose config, shell syntax, and whitespace validation passed; `deploy.sh` has executable mode 755.
- Work-unit commit: `1e73716` (`feat(deploy): unify monorepo compose workflow`).
- RDD delivery: the user explicitly disabled RDD for this clone; record outcome as `disabled/unmanaged`. No receipt or approval is claimed.

## Next Step
No further work remains for this feature. The pre-existing `microservicios_padawans.md` remains untouched.
