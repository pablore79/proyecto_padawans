import asyncio
from collections.abc import AsyncGenerator
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.alumno import Alumno
from app.models.asignacion_docente import AsignacionDocente
from app.models.curso import Curso
from app.models.inscripcion import EstadoInscripcion, Inscripcion
from app.models.materia import Materia
from app.models.usuario import RolUsuario, Usuario
from app.services.curso_service import CursoService
from app.services.inscripcion_service import InscripcionService

# Test database URL (uses same local Docker Postgres)
TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session with transaction rollback for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session() as session, session.begin():
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# --- Helper functions for creating test data ---


# Use short passwords to avoid bcrypt 72-byte limit
TEST_PASSWORD = "test1234"  # 8 chars minimum for validation


async def create_test_admin(db: AsyncSession) -> Usuario:
    """Create a test admin user."""
    admin = Usuario(
        username="admin_test",
        email="admin@test.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        rol=RolUsuario.ADMIN,
        activo=True,
    )
    db.add(admin)
    await db.flush()
    await db.refresh(admin)
    return admin


async def create_test_docente(db: AsyncSession) -> Usuario:
    """Create a test docente user."""
    docente = Usuario(
        username="docente_test",
        email="docente@test.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        rol=RolUsuario.DOCENTE,
        activo=True,
    )
    db.add(docente)
    await db.flush()
    await db.refresh(docente)
    return docente


async def create_test_alumno_user(db: AsyncSession, alumno: Alumno) -> Usuario:
    """Create a test alumno user linked to an alumno."""
    user = Usuario(
        username=f"alumno_{alumno.id}",
        email=alumno.email,
        password_hash=get_password_hash(TEST_PASSWORD),
        rol=RolUsuario.ALUMNO,
        alumno_id=alumno.id,
        activo=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_test_alumno(
    db: AsyncSession,
    dni: str = "12345678A",
    email: str = "alumno@test.com",
    nombre: str = "Juan",
    apellido: str = "Pérez",
    created_by: int = 1,
) -> Alumno:
    """Create a test alumno."""
    alumno = Alumno(
        dni=dni,
        nombre=nombre,
        apellido=apellido,
        email=email,
        telefono="123456789",
        fecha_nacimiento=date(2000, 1, 1),
        activo=True,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(alumno)
    await db.flush()
    await db.refresh(alumno)
    return alumno


async def create_test_curso(
    db: AsyncSession,
    nombre: str = "Curso Test",
    cupos: int = 20,
    created_by: int = 1,
) -> Curso:
    """Create a test curso."""
    curso = Curso(
        nombre=nombre,
        descripcion="Descripción de prueba",
        cupos=cupos,
        activo=True,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(curso)
    await db.flush()
    await db.refresh(curso)
    return curso


async def create_test_materia(
    db: AsyncSession,
    curso_id: int,
    nombre: str = "Materia Test",
    created_by: int = 1,
) -> Materia:
    """Create a test materia."""
    materia = Materia(
        curso_id=curso_id,
        nombre=nombre,
        descripcion="Descripción de prueba",
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(materia)
    await db.flush()
    await db.refresh(materia)
    return materia


async def create_test_inscripcion(
    db: AsyncSession,
    alumno_id: int,
    curso_id: int,
    estado: EstadoInscripcion = EstadoInscripcion.ACTIVA,
) -> Inscripcion:
    """Create a test inscripcion."""
    inscripcion = Inscripcion(
        alumno_id=alumno_id,
        curso_id=curso_id,
        estado=estado,
    )
    db.add(inscripcion)
    await db.flush()
    await db.refresh(inscripcion)
    return inscripcion


async def create_test_asignacion_docente(
    db: AsyncSession,
    usuario_id: int,
    curso_id: int,
) -> AsignacionDocente:
    """Create a test asignacion docente."""
    asignacion = AsignacionDocente(
        usuario_id=usuario_id,
        curso_id=curso_id,
    )
    db.add(asignacion)
    await db.flush()
    await db.refresh(asignacion)
    return asignacion


# --- Auth fixtures ---


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> Usuario:
    """Create and return admin user."""
    return await create_test_admin(db_session)


@pytest_asyncio.fixture
async def docente_user(db_session: AsyncSession) -> Usuario:
    """Create and return docente user."""
    return await create_test_docente(db_session)


@pytest_asyncio.fixture
async def alumno_user(db_session: AsyncSession) -> tuple[Usuario, Alumno]:
    """Create and return alumno user with linked alumno."""
    alumno = await create_test_alumno(db_session, dni="87654321B", email="alumno_user@test.com")
    user = await create_test_alumno_user(db_session, alumno)
    return user, alumno


@pytest_asyncio.fixture
async def auth_headers_admin(client: AsyncClient, admin_user: Usuario) -> dict[str, str]:
    """Get auth headers for admin user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers_docente(client: AsyncClient, docente_user: Usuario) -> dict[str, str]:
    """Get auth headers for docente user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": docente_user.username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers_alumno(
    client: AsyncClient, alumno_user: tuple[Usuario, Alumno]
) -> dict[str, str]:
    """Get auth headers for alumno user."""
    user, _ = alumno_user
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Data fixtures for integration tests ---


@pytest_asyncio.fixture
async def sample_alumno(db_session: AsyncSession, admin_user: Usuario) -> Alumno:
    """Create a sample alumno for tests."""
    return await create_test_alumno(db_session, created_by=admin_user.id)


@pytest_asyncio.fixture
async def sample_curso(db_session: AsyncSession, admin_user: Usuario) -> Curso:
    """Create a sample curso for tests."""
    return await create_test_curso(db_session, created_by=admin_user.id)


@pytest_asyncio.fixture
async def sample_materia(
    db_session: AsyncSession, sample_curso: Curso, admin_user: Usuario
) -> Materia:
    """Create a sample materia for tests."""
    return await create_test_materia(db_session, sample_curso.id, created_by=admin_user.id)


@pytest_asyncio.fixture
def curso_service(db_session: AsyncSession) -> CursoService:
    """Create CursoService instance for tests."""
    return CursoService(db_session)


@pytest_asyncio.fixture
def inscripcion_service(db_session: AsyncSession) -> InscripcionService:
    """Create InscripcionService instance for tests."""
    return InscripcionService(db_session)


@pytest_asyncio.fixture
async def sample_inscripcion(
    db_session: AsyncSession,
    sample_alumno: Alumno,
    sample_curso: Curso,
) -> Inscripcion:
    """Create a sample inscripcion for tests."""
    return await create_test_inscripcion(db_session, sample_alumno.id, sample_curso.id)


@pytest_asyncio.fixture
async def docente_with_curso(
    db_session: AsyncSession,
    docente_user: Usuario,
    sample_curso: Curso,
) -> tuple[Usuario, Curso]:
    """Create docente assigned to a curso."""
    await create_test_asignacion_docente(db_session, docente_user.id, sample_curso.id)
    return docente_user, sample_curso


@pytest_asyncio.fixture
async def alumno_with_inscripcion(
    db_session: AsyncSession,
    alumno_user: tuple[Usuario, Alumno],
    sample_curso: Curso,
) -> tuple[Usuario, Alumno, Curso]:
    """Create alumno with active inscripcion to a curso."""
    user, alumno = alumno_user
    await create_test_inscripcion(db_session, alumno.id, sample_curso.id)
    return user, alumno, sample_curso


# --- Cleanup fixture ---


@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_session: AsyncSession):
    """Auto-cleanup: runs before each test to ensure clean state."""
    # Tables are cleaned by transaction rollback in db_session fixture
    pass
