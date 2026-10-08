"""Pure tests for the database safety guard; no application or DB imports."""

import pytest

from safety_tests.database_guard import (
    DatabaseTarget,
    UnsafeTestDatabaseError,
    validate_test_database_config,
)

DEVELOPMENT_URL = "postgresql+psycopg://dev:secret@LOCALHOST/bunker4_alumnos"
SAFE_TEST_URL = "postgresql+psycopg://tester:secret@localhost:5432/bunker4_alumnos_test"


def validate(**overrides: str | None):
    values = {
        "test_database_url": SAFE_TEST_URL,
        "development_database_url": DEVELOPMENT_URL,
        "allow_reset": "true",
        "xdist_worker": None,
    }
    values.update(overrides)
    return validate_test_database_config(**values)


def test_rejects_missing_test_database_url() -> None:
    with pytest.raises(UnsafeTestDatabaseError, match="must be set explicitly"):
        validate(test_database_url=None)


def test_rejects_same_database_after_normalizing_driver_host_and_port() -> None:
    same_target = "postgresql+asyncpg://other:hidden@127.0.0.1:5432/bunker4_alumnos"

    with pytest.raises(UnsafeTestDatabaseError, match="different database"):
        validate(test_database_url=same_target)


def test_rejects_database_name_without_test_suffix() -> None:
    with pytest.raises(UnsafeTestDatabaseError, match="must end with '_test'"):
        validate(test_database_url="postgresql://tester:hidden@localhost/not_a_test_db")


def test_rejects_non_postgresql_dialect() -> None:
    with pytest.raises(UnsafeTestDatabaseError, match="must use PostgreSQL"):
        validate(test_database_url="sqlite:///bunker4_alumnos_test")


@pytest.mark.parametrize("authorization", [None, "", "TRUE", "1", "yes"])
def test_rejects_missing_or_inexact_reset_authorization(authorization: str | None) -> None:
    with pytest.raises(UnsafeTestDatabaseError, match="must be exactly 'true'"):
        validate(allow_reset=authorization)


def test_rejects_xdist_worker() -> None:
    with pytest.raises(UnsafeTestDatabaseError, match="xdist workers are not supported"):
        validate(xdist_worker="gw0")


def test_accepts_safe_postgresql_test_database() -> None:
    validated = validate()

    assert validated.url == SAFE_TEST_URL
    assert validated.target == DatabaseTarget(
        host="localhost", port=5432, database="bunker4_alumnos_test"
    )


def test_errors_do_not_reveal_credentials_or_complete_url() -> None:
    unsafe_url = "postgresql://sensitive_user:sensitive_password@localhost/bunker4_alumnos"

    with pytest.raises(UnsafeTestDatabaseError) as exc_info:
        validate(test_database_url=unsafe_url)

    message = str(exc_info.value)
    assert "sensitive_user" not in message
    assert "sensitive_password" not in message
    assert unsafe_url not in message
