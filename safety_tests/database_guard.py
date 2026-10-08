"""Fail-closed validation for destructive pytest database setup."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import parse_qs, unquote, urlsplit

RESET_AUTHORIZATION = "true"
TEST_DATABASE_SUFFIX = "_test"
_TARGET_OVERRIDE_QUERY_KEYS = frozenset({"database", "dbname", "host", "port"})
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class UnsafeTestDatabaseError(RuntimeError):
    """Raised when pytest database configuration is absent or unsafe."""


@dataclass(frozen=True)
class DatabaseTarget:
    """A credential-free database destination used for safety comparisons."""

    host: str
    port: int
    database: str


@dataclass(frozen=True)
class ValidatedTestDatabase:
    """A validated test URL plus its safe-to-display target metadata."""

    url: str = field(repr=False)
    target: DatabaseTarget


def _postgresql_target(url: str, variable_name: str) -> DatabaseTarget:
    if not url or url != url.strip():
        raise UnsafeTestDatabaseError(f"{variable_name} must be a non-empty, unambiguous URL")

    try:
        parsed = urlsplit(url)
        dialect = parsed.scheme.lower().split("+", maxsplit=1)[0]
        port = parsed.port or 5432
        host = parsed.hostname
    except ValueError as exc:
        raise UnsafeTestDatabaseError(f"{variable_name} is not a valid database URL") from exc

    if dialect != "postgresql":
        raise UnsafeTestDatabaseError(f"{variable_name} must use PostgreSQL")
    if host is None or not parsed.path.startswith("/") or parsed.fragment:
        raise UnsafeTestDatabaseError(f"{variable_name} must identify one PostgreSQL database")

    database = unquote(parsed.path[1:])
    if not database or "/" in database:
        raise UnsafeTestDatabaseError(f"{variable_name} must identify one PostgreSQL database")

    query_keys = set(parse_qs(parsed.query, keep_blank_values=True))
    if query_keys & _TARGET_OVERRIDE_QUERY_KEYS:
        raise UnsafeTestDatabaseError(
            f"{variable_name} must not override its database target in query parameters"
        )

    normalized_host = host.lower().rstrip(".")
    if normalized_host in _LOOPBACK_HOSTS:
        normalized_host = "localhost"

    return DatabaseTarget(host=normalized_host, port=port, database=database)


def validate_test_database_config(
    *,
    test_database_url: str | None,
    development_database_url: str,
    allow_reset: str | None,
    xdist_worker: str | None = None,
) -> ValidatedTestDatabase:
    """Validate all preconditions before a destructive test database reset."""
    if test_database_url is None or not test_database_url:
        raise UnsafeTestDatabaseError("TEST_DATABASE_URL must be set explicitly")
    if allow_reset != RESET_AUTHORIZATION:
        raise UnsafeTestDatabaseError(
            f"ALLOW_TEST_DATABASE_RESET must be exactly {RESET_AUTHORIZATION!r}"
        )
    if xdist_worker:
        raise UnsafeTestDatabaseError(
            "pytest-xdist workers are not supported by the shared test database fixture"
        )

    test_target = _postgresql_target(test_database_url, "TEST_DATABASE_URL")
    development_target = _postgresql_target(development_database_url, "DATABASE_URL")

    if test_target == development_target:
        raise UnsafeTestDatabaseError(
            "TEST_DATABASE_URL must target a different database than DATABASE_URL"
        )
    if not test_target.database.endswith(TEST_DATABASE_SUFFIX):
        raise UnsafeTestDatabaseError(
            f"TEST_DATABASE_URL database name must end with {TEST_DATABASE_SUFFIX!r}"
        )

    return ValidatedTestDatabase(url=test_database_url, target=test_target)


def validate_test_database_environment(
    development_database_url: str,
    environ: Mapping[str, str] | None = None,
) -> ValidatedTestDatabase:
    """Read and validate the test database contract from environment variables."""
    environment = os.environ if environ is None else environ
    return validate_test_database_config(
        test_database_url=environment.get("TEST_DATABASE_URL"),
        development_database_url=development_database_url,
        allow_reset=environment.get("ALLOW_TEST_DATABASE_RESET"),
        xdist_worker=environment.get("PYTEST_XDIST_WORKER"),
    )
