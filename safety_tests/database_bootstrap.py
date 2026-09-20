"""Validate pytest database safety before importing database-enabled application modules."""

import os

from app.core.config import settings
from safety_tests.database_guard import (
    ValidatedTestDatabase,
    validate_test_database_config,
    validate_test_database_environment,
)

TEST_DATABASE = validate_test_database_environment(settings.DATABASE_URL)


def require_safe_test_database() -> ValidatedTestDatabase:
    """Revalidate the captured URL before every destructive schema operation."""
    return validate_test_database_config(
        test_database_url=TEST_DATABASE.url,
        development_database_url=settings.DATABASE_URL,
        allow_reset=os.environ.get("ALLOW_TEST_DATABASE_RESET"),
        xdist_worker=os.environ.get("PYTEST_XDIST_WORKER"),
    )
