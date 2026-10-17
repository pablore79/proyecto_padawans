from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.deps import get_token
from app.api.v1 import routes
from app.main import app


class FakeBackendResponse:
    content = b'{"access_token":"test-token","token_type":"bearer"}'
    status_code = 200
    headers = {"content-type": "application/json"}

    @property
    def is_success(self) -> bool:
        return True


class FakeBackendClient:
    async def request(self, **_: object) -> FakeBackendResponse:
        return FakeBackendResponse()


async def fake_backend_client() -> AsyncGenerator[FakeBackendClient, None]:
    yield FakeBackendClient()


def test_login_stores_token_in_http_only_cookie() -> None:
    app.dependency_overrides[routes.get_backend_client] = fake_backend_client
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login", json={"username": "admin", "password": "password"}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["access_token"] == "test-token"
    assert "access_token=test-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]


def test_get_token_reads_bearer_token_before_cookie() -> None:
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"authorization", b"Bearer header-token"),
                (b"cookie", b"access_token=cookie-token"),
            ],
        }
    )

    assert get_token(request) == "header-token"


def test_get_token_reads_session_cookie() -> None:
    request = Request({"type": "http", "headers": [(b"cookie", b"access_token=cookie-token")]})

    assert get_token(request) == "cookie-token"


def test_logout_clears_session_cookie() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert 'access_token=""' in response.headers["set-cookie"]
