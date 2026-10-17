import pytest
from fastapi import HTTPException

from app.api.deps import require_role


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user", "allowed"),
    [
        ({"rol": "admin"}, True),
        ({"role": "admin"}, True),
        ({"rol": "admin", "role": "docente"}, True),
        ({"rol": "docente"}, False),
        ({"rol": "alumno"}, False),
        ({"rol": "docente", "role": "admin"}, False),
        ({"rol": None, "role": "admin"}, False),
        ({"rol": "", "role": "admin"}, False),
        ({"rol": ["admin"]}, False),
        ({}, False),
    ],
)
async def test_admin_role_precedence(user: dict[str, object], allowed: bool) -> None:
    guard = require_role("admin")

    if allowed:
        assert await guard(user=user) is user
    else:
        with pytest.raises(HTTPException) as caught:
            await guard(user=user)
        assert caught.value.status_code == 403
        assert caught.value.detail == "No tiene permisos para acceder a este recurso"
