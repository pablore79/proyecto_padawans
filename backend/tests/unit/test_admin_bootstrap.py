from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import UserCreate
from app.services.admin_bootstrap import (
    AdminBootstrapError,
    AdminBootstrapStatus,
    create_initial_admin,
)
from scripts.create_admin import collect_user_data


def _user_result(users: list[Usuario]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = users
    return result


def _session_with_matches(users: list[Usuario]) -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.execute.side_effect = [MagicMock(), _user_result(users)]
    return session


def _admin_data(password: str = "secure-password") -> UserCreate:
    return UserCreate(
        username="initial_admin",
        email="initial@example.com",
        password=password,
        rol=RolUsuario.ADMIN,
        alumno_id=None,
    )


async def test_create_initial_admin_hashes_password_and_self_audits(
    db_session: AsyncSession,
) -> None:
    result = await create_initial_admin(db_session, _admin_data())

    assert result.status == AdminBootstrapStatus.CREATED
    assert result.user.id is not None
    assert result.user.rol == RolUsuario.ADMIN
    assert result.user.alumno_id is None
    assert result.user.created_by == result.user.id
    assert result.user.updated_by == result.user.id
    assert verify_password("secure-password", result.user.password_hash)


async def test_create_initial_admin_is_idempotent_without_changing_password() -> None:
    original_hash = get_password_hash("original-password")
    existing = Usuario(
        id=7,
        username="initial_admin",
        email="initial@example.com",
        password_hash=original_hash,
        rol=RolUsuario.ADMIN,
        alumno_id=None,
    )
    session = _session_with_matches([existing])

    result = await create_initial_admin(session, _admin_data("different-password"))

    assert result.status == AdminBootstrapStatus.ALREADY_EXISTS
    assert result.user.password_hash == original_hash
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


async def test_create_initial_admin_rejects_a_different_existing_admin() -> None:
    existing = Usuario(
        id=7,
        username="other_admin",
        email="other@example.com",
        password_hash=get_password_hash("secure-password"),
        rol=RolUsuario.ADMIN,
        alumno_id=None,
    )
    session = _session_with_matches([existing])

    with pytest.raises(AdminBootstrapError, match="Ya existe otro administrador"):
        await create_initial_admin(session, _admin_data())

    session.add.assert_not_called()


@pytest.mark.parametrize(
    ("username", "email", "message"),
    [
        ("initial_admin", "other@example.com", "username"),
        ("other_user", "initial@example.com", "email"),
    ],
)
async def test_create_initial_admin_rejects_partial_collisions(
    username: str,
    email: str,
    message: str,
) -> None:
    existing = Usuario(
        id=8,
        username=username,
        email=email,
        password_hash=get_password_hash("secure-password"),
        rol=RolUsuario.DOCENTE,
        alumno_id=None,
    )
    session = _session_with_matches([existing])

    with pytest.raises(AdminBootstrapError, match=message):
        await create_initial_admin(session, _admin_data())

    session.add.assert_not_called()


def test_collect_user_data_uses_hidden_password_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    getpass_mock = MagicMock(side_effect=["secure-password", "secure-password"])
    monkeypatch.setattr("scripts.create_admin.getpass.getpass", getpass_mock)

    user_data = collect_user_data(" initial_admin ", " initial@example.com ")

    assert user_data.username == "initial_admin"
    assert user_data.email == "initial@example.com"
    assert user_data.password == "secure-password"
    assert getpass_mock.call_count == 2


def test_collect_user_data_rejects_password_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.create_admin.getpass.getpass",
        MagicMock(side_effect=["secure-password", "different-password"]),
    )

    with pytest.raises(AdminBootstrapError, match="no coinciden"):
        collect_user_data("initial_admin", "initial@example.com")


def test_collect_user_data_uses_existing_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.create_admin.getpass.getpass",
        MagicMock(side_effect=["short", "short"]),
    )

    with pytest.raises(ValidationError):
        collect_user_data("ab", "invalid-email")
