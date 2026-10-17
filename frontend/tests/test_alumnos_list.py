from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient

from app.api.deps import get_backend_client
from app.main import app


class FakeBackendResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.status_code = 200

    def json(self) -> dict[str, object]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class FakeBackendClient:
    async def get(
        self, url: str, *, headers: dict[str, str], params: dict[str, str] | None = None
    ) -> FakeBackendResponse:
        assert headers["Authorization"] == "Bearer admin-token"
        if url == "/api/v1/auth/me":
            return FakeBackendResponse({"id": 1, "username": "admin", "rol": "admin"})
        if url == "/api/v1/alumnos/1":
            return FakeBackendResponse(
                {
                    "id": 1,
                    "dni": "12345678",
                    "nombre": "Ada",
                    "apellido": "Lovelace",
                    "email": "ada@example.test",
                    "telefono": None,
                    "activo": True,
                }
            )
        assert url == "/api/v1/alumnos"
        assert params == {"search": "Ada"}
        return FakeBackendResponse(
            {
                "items": [
                    {
                        "id": 1,
                        "dni": "12345678",
                        "nombre": "Ada",
                        "apellido": "Lovelace",
                        "email": "ada@example.test",
                        "telefono": None,
                        "activo": True,
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0,
            }
        )


async def fake_backend_client() -> AsyncGenerator[FakeBackendClient, None]:
    yield FakeBackendClient()


def test_alumnos_list_renders_backend_items_for_authenticated_admin() -> None:
    app.dependency_overrides[get_backend_client] = fake_backend_client
    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", "admin-token")
            response = client.get("/alumnos/list", params={"search": "Ada"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "Lovelace, Ada" in response.text
    assert "12345678" in response.text


def test_alumno_edit_form_loads_existing_backend_values() -> None:
    app.dependency_overrides[get_backend_client] = fake_backend_client
    try:
        with TestClient(app) as client:
            client.cookies.set("access_token", "admin-token")
            response = client.get("/alumnos/1/editar")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "Editar Alumno" in response.text
    assert 'value="Ada"' in response.text
    assert 'value="ada@example.test"' in response.text
