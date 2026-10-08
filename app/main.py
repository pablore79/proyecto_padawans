from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.database import close_db, get_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestLogger, configure_logging, get_logger
from app.repositories.alumno_repo import AlumnoRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services.alumno_service import AlumnoService
from app.services.curso_service import CursoService
from app.services.inscripcion_service import InscripcionService

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    configure_logging(settings.LOG_LEVEL)
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de administración de alumnos para Bunker4",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

register_exception_handlers(app)
app.include_router(api_v1_router)


@app.middleware("http")
async def add_request_id(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    logger = RequestLogger(get_logger("http"))
    request_id = getattr(request.state, "request_id", str(uuid4()))
    start = perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000
        logger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )
        return response
    except Exception as e:
        duration_ms = (perf_counter() - start) * 1000
        logger.log_error(
            method=request.method,
            path=request.url.path,
            error=str(e),
            request_id=request_id,
        )
        raise


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/alumnos", response_class=HTMLResponse, include_in_schema=False)
async def alumnos_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("alumnos/list.html", {"request": request})


@app.get("/cursos", response_class=HTMLResponse, include_in_schema=False)
async def cursos_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("cursos/list.html", {"request": request})


@app.get("/cursos/{curso_id}", response_class=HTMLResponse, include_in_schema=False)
async def curso_detail(request: Request, curso_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        "cursos/detail.html", {"request": request, "curso_id": curso_id}
    )


@app.get("/alumnos/nuevo", response_class=HTMLResponse, include_in_schema=False)
async def alumno_nuevo(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("alumnos/_form.html", {"request": request, "alumno": None})


@app.get("/alumnos/{alumno_id}/editar", response_class=HTMLResponse, include_in_schema=False)
async def alumno_editar(
    request: Request,
    alumno_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AlumnoService(db)
    alumno = await service.get(alumno_id)
    return templates.TemplateResponse("alumnos/_form.html", {"request": request, "alumno": alumno})


@app.get("/alumnos/list", response_class=HTMLResponse, include_in_schema=False)
async def alumnos_list_partial(
    request: Request,
    activo: bool | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AlumnoService(db)
    from app.schemas.alumno import AlumnoListParams

    params = AlumnoListParams(activo=activo, search=search, limit=limit, offset=offset)
    result = await service.list(params)
    return templates.TemplateResponse(
        "alumnos/_row.html", {"request": request, "alumnos": result.items}
    )


@app.get("/alumnos/options", response_class=HTMLResponse, include_in_schema=False)
async def alumnos_options(
    request: Request, current_user=Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    repo = AlumnoRepository(db)
    alumnos = await repo.list(activo=True, limit=500, offset=0)
    return templates.TemplateResponse(
        "alumnos/_options.html", {"request": request, "alumnos": alumnos}
    )


@app.get("/cursos/nuevo", response_class=HTMLResponse, include_in_schema=False)
async def curso_nuevo(request: Request):
    return templates.TemplateResponse("cursos/_form.html", {"request": request, "curso": None})


@app.get("/cursos/{curso_id}/editar", response_class=HTMLResponse, include_in_schema=False)
async def curso_editar(
    request: Request,
    curso_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    curso = await service.get(curso_id)
    return templates.TemplateResponse("cursos/_form.html", {"request": request, "curso": curso})


@app.get("/cursos/list", response_class=HTMLResponse, include_in_schema=False)
async def cursos_list_partial(
    request: Request,
    activo: bool | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    result = await service.list(activo=activo, search=search, limit=limit, offset=offset)
    # Add inscriptos_count to each curso
    cursos_with_count = []
    for curso in result.items:
        inscriptos = await service.curso_repo.count_active_inscripciones(curso.id)
        curso.inscriptos_count = inscriptos
        cursos_with_count.append(curso)
    return templates.TemplateResponse(
        "cursos/_row.html", {"request": request, "cursos": cursos_with_count}
    )


@app.get("/cursos/{curso_id}/detalle", response_class=HTMLResponse, include_in_schema=False)
async def curso_detalle_partial(
    request: Request,
    curso_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    curso = await service.get(curso_id)
    inscriptos = await service.curso_repo.count_active_inscripciones(curso_id)
    curso.inscriptos_count = inscriptos
    return templates.TemplateResponse("cursos/detail.html", {"request": request, "curso": curso})


@app.get(
    "/cursos/{curso_id}/inscripciones/list", response_class=HTMLResponse, include_in_schema=False
)
async def inscripciones_list_partial(
    request: Request,
    curso_id: int,
    estado: str | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.inscripcion import EstadoInscripcion
    from app.schemas.inscripcion import InscripcionListParams

    service = InscripcionService(db)
    params = InscripcionListParams(
        estado=EstadoInscripcion(estado) if estado else None, limit=limit, offset=offset
    )
    result = await service.list_by_curso(curso_id, params)
    return templates.TemplateResponse(
        "cursos/_inscripcion_row.html",
        {"request": request, "inscripciones": result.items, "curso_id": curso_id},
    )


@app.get("/cursos/{curso_id}/inscribir", response_class=HTMLResponse, include_in_schema=False)
async def inscribir_alumno_form(
    request: Request,
    curso_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    curso = await service.get(curso_id)
    return templates.TemplateResponse(
        "cursos/_inscripcion_form.html",
        {"request": request, "curso_id": curso_id, "curso_nombre": curso.nombre},
    )


@app.get("/cursos/{curso_id}/materias/list", response_class=HTMLResponse, include_in_schema=False)
async def materias_list_partial(
    request: Request,
    curso_id: int,
    limit: int = 20,
    offset: int = 0,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    result = await service.list_materias(curso_id, limit, offset)
    return templates.TemplateResponse(
        "cursos/_materia_row.html",
        {"request": request, "materias": result.items, "curso_id": curso_id},
    )


@app.get("/cursos/{curso_id}/materias/nueva", response_class=HTMLResponse, include_in_schema=False)
async def materia_nueva_form(
    request: Request,
    curso_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return templates.TemplateResponse(
        "cursos/_materia_form.html", {"request": request, "curso_id": curso_id, "materia": None}
    )


@app.get(
    "/cursos/{curso_id}/materias/{materia_id}/editar",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def materia_editar_form(
    request: Request,
    curso_id: int,
    materia_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    materia = await service.get_materia(materia_id)
    return templates.TemplateResponse(
        "cursos/_materia_form.html", {"request": request, "curso_id": curso_id, "materia": materia}
    )


@app.get("/cursos/{curso_id}/docentes/list", response_class=HTMLResponse, include_in_schema=False)
async def docentes_list_partial(
    request: Request,
    curso_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.models.asignacion_docente import AsignacionDocente
    from app.models.usuario import Usuario

    query = (
        select(AsignacionDocente, Usuario)
        .join(Usuario, AsignacionDocente.usuario_id == Usuario.id)
        .where(AsignacionDocente.curso_id == curso_id)
    )
    result = await db.execute(query)
    rows = result.all()
    docentes = []
    for _ad, usuario in rows:
        docentes.append({"id": usuario.id, "username": usuario.username, "email": usuario.email})
    return templates.TemplateResponse(
        "cursos/_docente_row.html", {"request": request, "docentes": docentes, "curso_id": curso_id}
    )


@app.get(
    "/cursos/{curso_id}/docentes/asignar", response_class=HTMLResponse, include_in_schema=False
)
async def asignar_docente_form(
    request: Request,
    curso_id: int,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = CursoService(db)
    curso = await service.get(curso_id)
    return templates.TemplateResponse(
        "cursos/_docente_form.html",
        {"request": request, "curso_id": curso_id, "curso_nombre": curso.nombre},
    )


@app.get("/docentes/options", response_class=HTMLResponse, include_in_schema=False)
async def docentes_options(
    request: Request, current_user=Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    repo = UsuarioRepository(db)
    docentes = await repo.list_docentes(limit=500, offset=0)
    return templates.TemplateResponse(
        "docentes/_options.html", {"request": request, "docentes": docentes}
    )
