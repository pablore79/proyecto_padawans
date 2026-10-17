from collections.abc import AsyncGenerator, Callable
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request

from app.core.config import settings


async def get_backend_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get an async HTTP client for backend communication."""
    async with httpx.AsyncClient(base_url=settings.BACKEND_URL, timeout=30.0) as client:
        yield client


def get_token(request: Request) -> str | None:
    """Extract a bearer token from a request header or the session cookie."""
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.casefold() == "bearer" and token:
        return token
    return request.cookies.get("access_token")


async def get_current_user(
    request: Request,
    token: str | None = Depends(get_token),
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
) -> dict[str, Any]:
    """Get current user by validating token with backend."""
    if not token:
        raise HTTPException(
            status_code=401,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = await backend_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        response.raise_for_status()
        user_data: dict[str, Any] = response.json()
        request.state.user = user_data
        request.state.token = token
        return user_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Token inválido o expirado") from e
        raise HTTPException(status_code=502, detail="Error comunicándose con el backend") from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Backend no disponible") from e


def require_role(*allowed_roles: str) -> Callable[..., Any]:
    """Dependency factory for role-based access control."""

    async def role_checker(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = user.get("rol", user.get("role"))
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para acceder a este recurso",
            )
        return user

    return role_checker
