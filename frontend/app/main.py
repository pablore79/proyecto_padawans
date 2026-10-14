from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestLogger, configure_logging, get_logger

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(settings.LOG_LEVEL)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de administración de alumnos para Bunker4 - Frontend",
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
async def add_request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
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
