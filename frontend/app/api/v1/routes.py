import json
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from app.api.deps import get_backend_client, get_current_user, get_token, require_role

templates = Jinja2Templates(directory="templates")

router = APIRouter()


# Health check
@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "frontend"}


@router.post("/api/v1/auth/login")
async def login_proxy(
    request: Request,
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
) -> Response:
    """Proxy login and retain the issued token in a same-origin session cookie."""
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "authorization"}
    }

    try:
        backend_response = await backend_client.request(
            method=request.method,
            url="/api/v1/auth/login",
            headers=headers,
            content=await request.body(),
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Backend no disponible") from e

    response = Response(
        content=backend_response.content,
        status_code=backend_response.status_code,
        headers=dict(backend_response.headers),
        media_type=backend_response.headers.get("content-type"),
    )
    if backend_response.is_success:
        payload = json.loads(backend_response.content)
        access_token = payload.get("access_token") if isinstance(payload, dict) else None
        if isinstance(access_token, str):
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                samesite="lax",
                secure=request.url.scheme == "https",
            )
    return response


@router.post("/api/v1/auth/logout", status_code=204)
async def logout() -> Response:
    """Clear the same-origin session cookie."""
    response = Response(status_code=204)
    response.delete_cookie("access_token")
    return response


# Proxy all API calls to backend
@router.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_api(
    path: str,
    request: Request,
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
    token: str = Depends(get_token),
) -> Response:
    """Proxy all API requests to backend."""
    # Build headers
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "authorization"}
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Get query params
    params = dict(request.query_params)

    # Get body for non-GET/HEAD requests
    body: bytes | None = None
    if request.method not in ["GET", "HEAD"]:
        body = await request.body()

    try:
        response = await backend_client.request(
            method=request.method,
            url=f"/api/v1/{path}",
            headers=headers,
            params=params,
            content=body,
        )

        # Return response from backend
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type"),
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Backend no disponible") from e


# HTML Routes - serve templates
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request) -> Response:
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request, user: dict[str, Any] = Depends(get_current_user)) -> Response:
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


# Alumnos pages
@router.get("/alumnos", response_class=HTMLResponse, include_in_schema=False)
async def alumnos_page(
    request: Request, user: dict[str, Any] = Depends(require_role("admin"))
) -> Response:
    return templates.TemplateResponse("alumnos/list.html", {"request": request, "user": user})


@router.get("/alumnos/list", response_class=HTMLResponse, include_in_schema=False)
async def alumnos_list_partial(
    request: Request,
    user: dict[str, Any] = Depends(require_role("admin")),
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
    token: str | None = Depends(get_token),
) -> Response:
    """Render the alumno rows returned by the backend for HTMX requests."""
    if token is None:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        response = await backend_client.get(
            "/api/v1/alumnos",
            headers={"Authorization": f"Bearer {token}"},
            params=dict(request.query_params),
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="Error comunicándose con el backend") from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Backend no disponible") from e

    payload = response.json()
    alumnos = payload.get("items", []) if isinstance(payload, dict) else []
    return templates.TemplateResponse("alumnos/_row.html", {"request": request, "alumnos": alumnos})


@router.get("/alumnos/nuevo", response_class=HTMLResponse, include_in_schema=False)
async def alumno_nuevo(
    request: Request, user: dict[str, Any] = Depends(require_role("admin"))
) -> Response:
    context: dict[str, Any] = {"request": request, "alumno": None, "user": user}
    return templates.TemplateResponse("alumnos/_form.html", context)


@router.get("/alumnos/{alumno_id}/editar", response_class=HTMLResponse, include_in_schema=False)
async def alumno_editar(
    request: Request,
    alumno_id: int,
    user: dict[str, Any] = Depends(require_role("admin")),
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
    token: str | None = Depends(get_token),
) -> Response:
    """Load the alumno from the backend before rendering the edit form."""
    if token is None:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        response = await backend_client.get(
            f"/api/v1/alumnos/{alumno_id}", headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="Error comunicándose con el backend") from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Backend no disponible") from e

    context = {"request": request, "alumno": response.json(), "user": user}
    return templates.TemplateResponse("alumnos/_form.html", context)


# Cursos pages
@router.get("/cursos", response_class=HTMLResponse, include_in_schema=False)
async def cursos_page(
    request: Request, user: dict[str, Any] = Depends(require_role("admin"))
) -> Response:
    return templates.TemplateResponse("cursos/list.html", {"request": request, "user": user})


@router.get("/cursos/nuevo", response_class=HTMLResponse, include_in_schema=False)
async def curso_nuevo(
    request: Request, user: dict[str, Any] = Depends(require_role("admin"))
) -> Response:
    context = {"request": request, "curso": None, "user": user}
    return templates.TemplateResponse("cursos/_form.html", context)


@router.get("/cursos/{curso_id}/editar", response_class=HTMLResponse, include_in_schema=False)
async def curso_editar(
    request: Request,
    curso_id: int,
    user: dict[str, Any] = Depends(require_role("admin")),
    backend_client: httpx.AsyncClient = Depends(get_backend_client),
    token: str | None = Depends(get_token),
) -> Response:
    """Load the curso from the backend before rendering the edit form."""
    if token is None:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        response = await backend_client.get(
            f"/api/v1/cursos/{curso_id}", headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail="Error comunicándose con el backend") from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Backend no disponible") from e

    context = {"request": request, "curso": response.json(), "user": user}
    return templates.TemplateResponse("cursos/_form.html", context)


@router.get("/cursos/{curso_id}", response_class=HTMLResponse, include_in_schema=False)
async def curso_detail(
    request: Request, curso_id: int, user: dict[str, Any] = Depends(require_role("admin"))
) -> Response:
    context = {"request": request, "curso_id": curso_id, "user": user}
    return templates.TemplateResponse("cursos/detail.html", context)


# Docente pages
@router.get("/docente/me/cursos", response_class=HTMLResponse, include_in_schema=False)
async def docente_mis_cursos(
    request: Request, user: dict[str, Any] = Depends(require_role("docente"))
) -> Response:
    return templates.TemplateResponse("docente/mis_cursos.html", {"request": request, "user": user})


# Alumno pages
@router.get("/alumno/me/cursos", response_class=HTMLResponse, include_in_schema=False)
async def alumno_mis_cursos(
    request: Request, user: dict[str, Any] = Depends(require_role("alumno"))
) -> Response:
    return templates.TemplateResponse("alumno/mis_cursos.html", {"request": request, "user": user})
