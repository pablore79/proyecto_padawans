import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.alumno import Alumno
from app.models.inscripcion import EstadoInscripcion
from app.schemas.inscripcion import InscripcionCreate, InscripcionListParams
from app.services.curso_service import CursoService
from app.services.inscripcion_service import InscripcionService


class TestInscripcionService:
    """Unit tests for InscripcionService."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> InscripcionService:
        return InscripcionService(db_session)

    @pytest.fixture
    def inscripcion_data(self, sample_alumno, sample_curso) -> InscripcionCreate:
        return InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)

    # --- CREATE tests ---

    async def test_create_inscripcion_success(
        self, service: InscripcionService, inscripcion_data: InscripcionCreate
    ):
        """Test successful inscripcion creation."""
        created = await service.create(inscripcion_data)

        assert created.id is not None
        assert created.alumno_id == inscripcion_data.alumno_id
        assert created.curso_id == inscripcion_data.curso_id
        assert created.estado == EstadoInscripcion.ACTIVA

    async def test_create_inscripcion_alumno_not_found(self, service: InscripcionService):
        """Test creating inscripcion for non-existent alumno raises NotFoundError."""
        data = InscripcionCreate(alumno_id=99999, curso_id=1)
        with pytest.raises(NotFoundError) as exc:
            await service.create(data)

        assert exc.value.code == "alumno_no_encontrado"

    async def test_create_inscripcion_curso_not_found(
        self, service: InscripcionService, sample_alumno
    ):
        """Test creating inscripcion for non-existent curso raises NotFoundError."""
        data = InscripcionCreate(alumno_id=sample_alumno.id, curso_id=99999)
        with pytest.raises(NotFoundError) as exc:
            await service.create(data)

        assert exc.value.code == "curso_no_encontrado"

    async def test_create_inscripcion_alumno_inactivo_fails(
        self, service: InscripcionService, db_session: AsyncSession, sample_curso: AsyncSession
    ):
        """Test creating inscripcion for inactive alumno raises ConflictError."""
        from app.models.alumno import Alumno

        # Create inactive alumno
        alumno = Alumno(
            dni="99999999Z",
            nombre="Inactivo",
            apellido="Test",
            email="inactivo@test.com",
            activo=False,
            created_by=1,
            updated_by=1,
        )
        db_session.add(alumno)
        await db_session.flush()
        await db_session.refresh(alumno)

        data = InscripcionCreate(alumno_id=alumno.id, curso_id=sample_curso.id)
        with pytest.raises(ConflictError) as exc:
            await service.create(data)

        assert exc.value.code == "alumno_inactivo"

    async def test_create_inscripcion_curso_inactivo_fails(
        self, service: InscripcionService, db_session: AsyncSession, sample_alumno
    ):
        """Test creating inscripcion for inactive curso raises ConflictError."""
        from app.models.curso import Curso

        curso = Curso(
            nombre="Inactivo",
            cupos=20,
            activo=False,
            created_by=1,
            updated_by=1,
        )
        db_session.add(curso)
        await db_session.flush()
        await db_session.refresh(curso)

        data = InscripcionCreate(alumno_id=sample_alumno.id, curso_id=curso.id)
        with pytest.raises(ConflictError) as exc:
            await service.create(data)

        assert exc.value.code == "curso_inactivo"

    async def test_create_inscripcion_duplicate_active_fails(
        self, service: InscripcionService, inscripcion_data: InscripcionCreate
    ):
        """Test creating duplicate active inscripcion raises ConflictError."""
        await service.create(inscripcion_data)

        with pytest.raises(ConflictError) as exc:
            await service.create(inscripcion_data)

        assert exc.value.code == "inscripcion_duplicada"

    async def test_create_inscripcion_allow_duplicate_after_baja(
        self, service: InscripcionService, inscripcion_data: InscripcionCreate
    ):
        """Test creating inscripcion after previous one is baja is allowed."""
        created = await service.create(inscripcion_data)
        await service.set_baja(created.curso_id, created.alumno_id)

        # Now create again - should succeed
        new_inscripcion = await service.create(inscripcion_data)
        assert new_inscripcion.estado == EstadoInscripcion.ACTIVA
        assert new_inscripcion.id != created.id

    async def test_create_inscripcion_cupo_lleno_fails(
        self, service: InscripcionService, db_session: AsyncSession, sample_alumno
    ):
        """Test creating inscripcion when curso is full raises ConflictError."""
        from app.models.curso import Curso

        # Create curso with cupos=1
        curso = Curso(
            nombre="Cupo 1",
            cupos=1,
            activo=True,
            created_by=1,
            updated_by=1,
        )
        db_session.add(curso)
        await db_session.flush()
        await db_session.refresh(curso)

        # Create another alumno
        alumno2 = Alumno(
            dni="88888888Y",
            nombre="Otro",
            apellido="Alumno",
            email="otro@test.com",
            activo=True,
            created_by=1,
            updated_by=1,
        )
        db_session.add(alumno2)
        await db_session.flush()
        await db_session.refresh(alumno2)

        # First inscripcion - should succeed
        data1 = InscripcionCreate(alumno_id=sample_alumno.id, curso_id=curso.id)
        await service.create(data1)

        # Second inscripcion - should fail
        data2 = InscripcionCreate(alumno_id=alumno2.id, curso_id=curso.id)
        with pytest.raises(ConflictError) as exc:
            await service.create(data2)

        assert exc.value.code == "cupos_completos"

    # --- GET tests ---

    async def test_get_inscripcion_success(
        self, service: InscripcionService, inscripcion_data: InscripcionCreate
    ):
        """Test successful inscripcion retrieval."""
        created = await service.create(inscripcion_data)
        retrieved = await service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.alumno_id == created.alumno_id

    async def test_get_inscripcion_not_found(self, service: InscripcionService):
        """Test getting non-existent inscripcion raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc:
            await service.get(99999)

        assert exc.value.code == "inscripcion_no_encontrada"

    # --- LIST BY CURSO tests ---

    async def test_list_by_curso_empty(self, service: InscripcionService, sample_curso):
        """Test listing inscripciones for curso with none."""
        params = InscripcionListParams(limit=20, offset=0)
        result = await service.list_by_curso(sample_curso.id, params)

        assert result.items == []
        assert result.total == 0

    async def test_list_by_curso_with_data(
        self, service: InscripcionService, sample_alumno, sample_curso
    ):
        """Test listing inscripciones for curso with data."""
        await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )

        # Create another alumno
        from app.models.alumno import Alumno

        alumno2 = Alumno(
            dni="77777777X",
            nombre="Segundo",
            apellido="Alumno",
            email="segundo@test.com",
            activo=True,
            created_by=1,
            updated_by=1,
        )
        service.db.add(alumno2)
        await service.db.flush()
        await service.db.refresh(alumno2)

        await service.create(InscripcionCreate(alumno_id=alumno2.id, curso_id=sample_curso.id))

        params = InscripcionListParams(limit=20, offset=0)
        result = await service.list_by_curso(sample_curso.id, params)

        assert len(result.items) == 2
        assert result.total == 2

    async def test_list_by_curso_filter_estado(
        self, service: InscripcionService, sample_alumno, sample_curso
    ):
        """Test filtering inscripciones by estado."""
        _ = await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )
        await service.set_baja(sample_curso.id, sample_alumno.id)

        params = InscripcionListParams(estado=EstadoInscripcion.ACTIVA, limit=20, offset=0)
        result = await service.list_by_curso(sample_curso.id, params)
        assert len(result.items) == 0

        params = InscripcionListParams(estado=EstadoInscripcion.BAJA, limit=20, offset=0)
        result = await service.list_by_curso(sample_curso.id, params)
        assert len(result.items) == 1
        assert result.items[0].estado == EstadoInscripcion.BAJA

    # --- LIST BY ALUMNO tests ---

    async def test_list_by_alumno_empty(self, service: InscripcionService, sample_alumno):
        """Test listing inscripciones for alumno with none."""
        params = InscripcionListParams(limit=20, offset=0)
        result = await service.list_by_alumno(sample_alumno.id, params)

        assert result.items == []
        assert result.total == 0

    # --- SET BAJA tests ---

    async def test_set_baja_success(self, service: InscripcionService, sample_alumno, sample_curso):
        """Test successful baja of inscripcion."""
        created = await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )

        updated = await service.set_baja(sample_curso.id, sample_alumno.id)

        assert updated.estado == EstadoInscripcion.BAJA
        assert updated.id == created.id

    async def test_set_baja_not_found(self, service: InscripcionService, sample_curso):
        """Test setting baja for non-existent inscripcion raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc:
            await service.set_baja(sample_curso.id, 99999)

        assert exc.value.code == "inscripcion_no_encontrada"

    async def test_set_baja_already_baja_fails(
        self, service: InscripcionService, sample_alumno, sample_curso
    ):
        """Test setting baja on already baja inscripcion raises NotFoundError (no active)."""
        await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )
        await service.set_baja(sample_curso.id, sample_alumno.id)

        with pytest.raises(NotFoundError) as exc:
            await service.set_baja(sample_curso.id, sample_alumno.id)

        assert exc.value.code == "inscripcion_no_encontrada"

    # --- GET CURSOS DOCENTE tests ---

    async def test_get_cursos_docente_empty(self, service: InscripcionService, docente_user):
        """Test getting cursos for docente with none assigned."""
        result = await service.get_cursos_docente(docente_user.id)

        assert result == []

    async def test_get_cursos_docente_with_data(
        self, service: InscripcionService, docente_user, sample_curso, sample_alumno
    ):
        """Test getting cursos for docente with assigned curso and alumnos."""

        # Assign docente to curso
        await service.asignar_docente(sample_curso.id, docente_user.id)

        # Create inscripcion
        await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )

        result = await service.get_cursos_docente(docente_user.id)

        assert len(result) == 1
        assert result[0]["curso"].id == sample_curso.id
        assert len(result[0]["alumnos"]) == 1
        assert result[0]["alumnos"][0]["alumno_id"] == sample_alumno.id

    async def test_get_cursos_docente_only_active_cursos(
        self,
        service: InscripcionService,
        curso_service: CursoService,
        docente_user,
        sample_curso,
        admin_user,
    ):
        """Test that inactive cursos are not returned for docente."""

        # Assign docente to active curso
        await service.asignar_docente(sample_curso.id, docente_user.id)

        # Verify it's returned when active
        result = await service.get_cursos_docente(docente_user.id)
        assert len(result) == 1

        # Deactivate curso (this should desasignar docente per PRD regla 5)
        await curso_service.soft_delete(sample_curso.id, admin_user.id)

        # Now docente should not see the curso
        result = await service.get_cursos_docente(docente_user.id)
        assert len(result) == 0

    async def test_asignar_docente_rejects_inactive_curso(
        self, service: InscripcionService, docente_user, db_session
    ):
        """Test that assigning docente to inactive curso raises ConflictError."""
        from app.models.curso import Curso

        curso_inactivo = Curso(
            nombre="Inactivo",
            cupos=20,
            activo=False,
            created_by=1,
            updated_by=1,
        )
        db_session.add(curso_inactivo)
        await db_session.flush()
        await db_session.refresh(curso_inactivo)

        from app.core.exceptions import ConflictError

        with pytest.raises(ConflictError) as exc:
            await service.asignar_docente(curso_inactivo.id, docente_user.id)
        assert exc.value.code == "curso_inactivo"

    # --- GET CURSOS ALUMNO tests ---

    async def test_get_cursos_alumno_empty(self, service: InscripcionService, sample_alumno):
        """Test getting cursos for alumno with none."""
        result = await service.get_cursos_alumno(sample_alumno.id)

        assert result == []

    async def test_get_cursos_alumno_with_data(
        self, service: InscripcionService, sample_alumno, sample_curso
    ):
        """Test getting cursos for alumno with active inscripcion."""
        await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )

        result = await service.get_cursos_alumno(sample_alumno.id)

        assert len(result) == 1
        assert result[0]["curso"].id == sample_curso.id
        assert result[0]["inscripcion"].estado == EstadoInscripcion.ACTIVA

    async def test_get_cursos_alumno_only_active_inscripciones(
        self, service: InscripcionService, sample_alumno, sample_curso
    ):
        """Test that only active inscripciones are returned."""
        _ = await service.create(
            InscripcionCreate(alumno_id=sample_alumno.id, curso_id=sample_curso.id)
        )
        await service.set_baja(sample_curso.id, sample_alumno.id)

        result = await service.get_cursos_alumno(sample_alumno.id)
        assert len(result) == 0

    # --- ASIGNAR DOCENTE tests ---

    async def test_asignar_docente_success(
        self, service: InscripcionService, docente_user, sample_curso
    ):
        """Test successful docente assignment."""
        result = await service.asignar_docente(sample_curso.id, docente_user.id)

        assert result["curso_id"] == sample_curso.id
        assert result["usuario_id"] == docente_user.id

    async def test_asignar_docente_curso_not_found(self, service: InscripcionService, docente_user):
        """Test assigning docente to non-existent curso raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc:
            await service.asignar_docente(99999, docente_user.id)

        assert exc.value.code == "curso_no_encontrado"

    async def test_asignar_docente_usuario_not_found(
        self, service: InscripcionService, sample_curso
    ):
        """Test assigning non-existent usuario raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc:
            await service.asignar_docente(sample_curso.id, 99999)

        assert exc.value.code == "usuario_no_encontrado"

    async def test_asignar_docente_usuario_not_docente_fails(
        self, service: InscripcionService, admin_user, sample_curso
    ):
        """Test assigning non-docente user raises ConflictError."""
        with pytest.raises(ConflictError) as exc:
            await service.asignar_docente(sample_curso.id, admin_user.id)

        assert exc.value.code == "usuario_no_es_docente"

    async def test_asignar_docente_duplicate_fails(
        self, service: InscripcionService, docente_user, sample_curso
    ):
        """Test assigning same docente twice raises ConflictError."""
        await service.asignar_docente(sample_curso.id, docente_user.id)

        with pytest.raises(ConflictError) as exc:
            await service.asignar_docente(sample_curso.id, docente_user.id)

        assert exc.value.code == "docente_ya_asignado"

    # --- DESASIGNAR DOCENTE tests ---

    async def test_desasignar_docente_success(
        self, service: InscripcionService, docente_user, sample_curso
    ):
        """Test successful docente deassignment."""
        await service.asignar_docente(sample_curso.id, docente_user.id)
        await service.desasignar_docente(sample_curso.id, docente_user.id)

        # Verify removed
        from sqlalchemy import select

        from app.models.asignacion_docente import AsignacionDocente

        result = await service.db.execute(
            select(AsignacionDocente).where(
                AsignacionDocente.usuario_id == docente_user.id,
                AsignacionDocente.curso_id == sample_curso.id,
            )
        )
        assert result.scalar_one_or_none() is None

    async def test_desasignar_docente_not_found(
        self, service: InscripcionService, docente_user, sample_curso
    ):
        """Test deassigning non-existent assignment raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc:
            await service.desasignar_docente(sample_curso.id, docente_user.id)

        assert exc.value.code == "asignacion_no_encontrada"
