from collections.abc import AsyncGenerator, Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_backend_client
from app.main import app


@pytest.fixture
def session_probe() -> Generator[tuple[TestClient, list[httpx.Request]], None, None]:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 1, "username": "admin", "rol": "admin"})

    async def backend() -> AsyncGenerator[httpx.AsyncClient, None]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://backend"
        ) as client:
            yield client

    app.dependency_overrides[get_backend_client] = backend
    try:
        with TestClient(app) as client:
            yield client, seen
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER"])
def test_explicit_bearer_remains_case_insensitive(
    session_probe: tuple[TestClient, list[httpx.Request]], scheme: str
) -> None:
    client, seen = session_probe

    response = client.get("/dashboard", headers={"Authorization": f"{scheme} explicit"})

    assert response.status_code == 200
    assert seen[-1].headers["authorization"] == "Bearer explicit"


def test_proxy_sends_exactly_one_authorization(
    session_probe: tuple[TestClient, list[httpx.Request]],
) -> None:
    client, seen = session_probe
    client.cookies.set("access_token", "cookie-token")

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer explicit"})

    assert response.status_code == 200
    assert seen[-1].headers.get_list("authorization") == ["Bearer explicit"]


def test_admin_session_can_access_alumnos_page(
    session_probe: tuple[TestClient, list[httpx.Request]],
) -> None:
    client, _ = session_probe
    client.cookies.set("access_token", "admin-token")

    response = client.get("/alumnos")

    assert response.status_code == 200
