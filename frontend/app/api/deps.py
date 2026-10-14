from collections.abc import AsyncGenerator, Callable
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

security = HTTPBearer(auto_error=False)


async def get_backend_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Get an async HTTP client for backend communication."""
    async with httpx.AsyncClient(base_url=settings.BACKEND_URL, timeout=30.0) as client:
        yield client


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
) -> dict[str, Any]:
    """Get current user by validating token with backend."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = await backend_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        response.raise_for_status()
        user_data: dict[str, Any] = response.json()
        request.state.user = user_data
        request.state.token = credentials.credentials
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
        user_role = user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="No tiene permisos para acceder a este recurso",
            )
        return user

    return role_checker


def get_token(request: Request) -> str | None:
    """Extract token from request state."""
    return getattr(request.state, "token", None)
