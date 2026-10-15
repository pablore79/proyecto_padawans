# Admin Bootstrap and Docker Helpers

## Objective
Make the backend admin bootstrap module available in its image and provide root scripts to build and stop the monorepo Compose project.

## Problem and Why
The backend Docker ignore file excludes `scripts/`, which removes `scripts.create_admin` from the build context. Root build and shutdown commands are also not yet wrapped in convenient scripts.

## Scope and Constraints
- Remove only the `scripts/` exclusion from `backend/.dockerignore`.
- Add executable root `build.sh` to build Compose services from any working directory.
- Add executable root `down.sh` to stop/remove Compose services without deleting named volumes.
- Update `DEPLOY.md` with the helper commands and administrator bootstrap command.
- Preserve the user's untracked `microservicios_padawans.md` untouched and exclude it from commits.
- Do not deploy/start/stop containers or build Docker images during this task.

## Delivery Strategy
- Strategy: ask-on-risk (default); forecast is below the ~400 authored-line budget.
- Route: delegated direct implementation; implementation touches several operational files and docs.
- Trigger evidence: Docker build-context configuration, two new executable scripts, and deployment guide changes.
- TDD exception: no meaningful runnable RED test exists for these shell/config/docs changes; validate shell syntax and Compose configuration after implementation.
- RDD: explicitly disabled for this clone by the user; delivery outcome is disabled/unmanaged.

## Tasks
- [x] A1 — Include the admin bootstrap package in the backend image build context and add root build/down helpers.
- [x] A2 — Document build, stop, rebuild, and first-admin commands in `DEPLOY.md`.
- [x] A3 — Validate scripts and Compose configuration and inspect the scoped diff. The Conventional Commit work unit remains pending for the parent.

## Acceptance Criteria
- `backend/scripts/` is no longer excluded by `backend/.dockerignore`.
- `build.sh` builds Compose images using the canonical root Compose file from any current directory.
- `down.sh` stops/removes the Compose project and cannot pass `-v` or otherwise remove persistent volumes.
- Documentation shows how to rebuild backend, recreate it, and run `python -m scripts.create_admin` inside it.
- Shell syntax and Compose configuration checks pass; changes are committed on the current feature branch.

## Checks
- `bash -n build.sh down.sh`.
- `docker compose -f docker-compose.yml config --quiet` (do not expose rendered environment values).
- `git diff --check`, inspect final scoped diff and file modes.
- Do not run Docker image builds or container lifecycle operations in this task.

## Progress and Evidence
- Root cause confirmed: `backend/.dockerignore` excludes `scripts/` at line 68, although `backend/scripts/create_admin.py` is the intended admin module.
- Prior deployment-unification task closed in commit `c8adc9b`; implementation commit was `1e73716`.
- RDD is off for this clone by explicit user request; no native review or approval will be claimed.
- Removed only the `scripts/` build-context exclusion. Added executable `build.sh`, which resolves the repository Compose file and forwards optional build service arguments, and `down.sh`, which runs `docker compose down` without forwarding arguments.
- Updated `DEPLOY.md` with build, safe shutdown, backend recreation, and interactive first-administrator instructions without example credentials.
- Validation passed: `bash -n build.sh down.sh`; `docker compose -f docker-compose.yml config --quiet`; and `git diff --check`. The shell reported only the existing Conda activation warning that `PYTHONNOUSERSITE` was overwritten.
- File-mode inspection confirms `build.sh` and `down.sh` are executable (`755`); changed documentation and configuration files remain `644`.
- No Docker image build, container lifecycle operation, or network operation was run.
- Commit hash: pending parent-owned commit.

## Next Step
Let the parent create the Conventional Commit work unit and record its identity.
