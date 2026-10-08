import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.alumno import AlumnoCreate, AlumnoListParams, AlumnoUpdate
from app.services.alumno_service import AlumnoService


class TestAlumnoService:
    """Unit tests for AlumnoService."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> AlumnoService:
        return AlumnoService(db_session)

    @pytest.fixture
    def alumno_data(self) -> AlumnoCreate:
        return AlumnoCreate(
            dni="11111111A",
            nombre="Test",
            apellido="User",
            email="test@test.com",
            telefono="123456789",
            fecha_nacimiento="2000-01-01",
        )

    # --- CREATE tests ---

    async def test_create_alumno_success(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test successful alumno creation."""
        created = await service.create(alumno_data, current_user_id=1)

        assert created.id is not None
        assert created.dni == alumno_data.dni
        assert created.nombre == alumno_data.nombre
        assert created.apellido == alumno_data.apellido
        assert created.email == alumno_data.email
        assert created.activo is True

    async def test_create_alumno_duplicate_dni_fails(
        self, service: AlumnoService, alumno_data: AlumnoCreate
    ):
        """Test that duplicate DNI raises ConflictError."""
        await service.create(alumno_data, current_user_id=1)

        duplicate_data = alumno_data.model_copy(update={"email": "different@test.com"})
        with pytest.raises(ConflictError) as exc:
            await service.create(duplicate_data, current_user_id=1)

        assert exc.value.code == "dni_duplicado"

    async def test_create_alumno_duplicate_email_fails(
        self, service: AlumnoService, alumno_data: AlumnoCreate
    ):
        """Test that duplicate email raises ConflictError."""
        await service.create(alumno_data, current_user_id=1)

        duplicate_data = alumno_data.model_copy(update={"dni": "22222222B"})
        with pytest.raises(ConflictError) as exc:
            await service.create(duplicate_data, current_user_id=1)

        assert exc.value.code == "email_duplicado"

    # --- GET tests ---

    async def test_get_alumno_success(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test successful alumno retrieval."""
        created = await service.create(alumno_data, current_user_id=1)
        retrieved = await service.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.dni == created.dni

    async def test_get_alumno_not_found(self, service: AlumnoService):
        """Test that getting non-existent alumno raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc:
            await service.get(99999)

        assert exc.value.code == "alumno_no_encontrado"

    # --- LIST tests ---

    async def test_list_alumnos_empty(self, service: AlumnoService):
        """Test listing alumnos when empty."""
        params = AlumnoListParams(limit=20, offset=0)
        result = await service.list(params)

        assert result.items == []
        assert result.total == 0

    async def test_list_alumnos_with_data(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test listing alumnos with data."""
        await service.create(alumno_data, current_user_id=1)
        await service.create(
            alumno_data.model_copy(update={"dni": "22222222B", "email": "test2@test.com"}),
            current_user_id=1,
        )

        params = AlumnoListParams(limit=20, offset=0)
        result = await service.list(params)

        assert len(result.items) == 2
        assert result.total == 2

    async def test_list_alumnos_filter_activo(
        self, service: AlumnoService, alumno_data: AlumnoCreate
    ):
        """Test filtering by activo status."""
        await service.create(alumno_data, current_user_id=1)
        await service.create(
            alumno_data.model_copy(update={"dni": "22222222B", "email": "test2@test.com"}),
            current_user_id=1,
        )

        # Soft delete one
        created = await service.alumno_repo.get_by_dni(alumno_data.dni)
        await service.soft_delete(created.id, current_user_id=1)

        params = AlumnoListParams(activo=True, limit=20, offset=0)
        result = await service.list(params)

        assert len(result.items) == 1
        assert result.items[0].activo is True

    async def test_list_alumnos_search(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test search by DNI/nombre/apellido."""
        await service.create(alumno_data, current_user_id=1)
        await service.create(
            alumno_data.model_copy(
                update={"dni": "22222222B", "email": "test2@test.com", "nombre": "Otro"}
            ),
            current_user_id=1,
        )

        params = AlumnoListParams(search="Test", limit=20, offset=0)
        result = await service.list(params)

        assert len(result.items) == 1
        assert result.items[0].nombre == "Test"

    async def test_list_alumnos_pagination(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test pagination."""
        for i in range(5):
            await service.create(
                alumno_data.model_copy(
                    update={"dni": f"{i}1111111A", "email": f"test{i}@test.com"}
                ),
                current_user_id=1,
            )

        params = AlumnoListParams(limit=2, offset=0)
        result = await service.list(params)
        assert len(result.items) == 2
        assert result.total == 5

        params = AlumnoListParams(limit=2, offset=2)
        result = await service.list(params)
        assert len(result.items) == 2

    # --- UPDATE tests ---

    async def test_update_alumno_success(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test successful alumno update."""
        created = await service.create(alumno_data, current_user_id=1)

        update_data = AlumnoUpdate(nombre="Updated", telefono="987654321")
        updated = await service.update(created.id, update_data, current_user_id=1)

        assert updated.nombre == "Updated"
        assert updated.telefono == "987654321"
        assert updated.dni == created.dni  # unchanged

    async def test_update_alumno_not_found(self, service: AlumnoService):
        """Test updating non-existent alumno raises NotFoundError."""
        update_data = AlumnoUpdate(nombre="Updated")
        with pytest.raises(NotFoundError):
            await service.update(99999, update_data, current_user_id=1)

    async def test_update_alumno_duplicate_dni_fails(
        self, service: AlumnoService, alumno_data: AlumnoCreate
    ):
        """Test updating to duplicate DNI raises ConflictError."""
        created1 = await service.create(alumno_data, current_user_id=1)
        created2 = await service.create(
            alumno_data.model_copy(update={"dni": "22222222B", "email": "test2@test.com"}),
            current_user_id=1,
        )

        update_data = AlumnoUpdate(dni=created1.dni)
        with pytest.raises(ConflictError) as exc:
            await service.update(created2.id, update_data, current_user_id=1)

        assert exc.value.code == "dni_duplicado"

    async def test_update_alumno_duplicate_email_fails(
        self, service: AlumnoService, alumno_data: AlumnoCreate
    ):
        """Test updating to duplicate email raises ConflictError."""
        created1 = await service.create(alumno_data, current_user_id=1)
        created2 = await service.create(
            alumno_data.model_copy(update={"dni": "22222222B", "email": "test2@test.com"}),
            current_user_id=1,
        )

        update_data = AlumnoUpdate(email=created1.email)
        with pytest.raises(ConflictError) as exc:
            await service.update(created2.id, update_data, current_user_id=1)

        assert exc.value.code == "email_duplicado"

    # --- SOFT DELETE tests ---

    async def test_soft_delete_success(self, service: AlumnoService, alumno_data: AlumnoCreate):
        """Test successful soft delete."""
        created = await service.create(alumno_data, current_user_id=1)
        deleted = await service.soft_delete(created.id, current_user_id=1)

        assert deleted.activo is False
        assert deleted.id == created.id

    async def test_soft_delete_not_found(self, service: AlumnoService):
        """Test soft deleting non-existent alumno raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await service.soft_delete(99999, current_user_id=1)

    async def test_soft_delete_already_inactive_fails(
        self, service: AlumnoService, alumno_data: AlumnoCreate
    ):
        """Test soft deleting already inactive alumno raises ConflictError."""
        created = await service.create(alumno_data, current_user_id=1)
        await service.soft_delete(created.id, current_user_id=1)

        with pytest.raises(ConflictError) as exc:
            await service.soft_delete(created.id, current_user_id=1)

        assert exc.value.code == "alumno_ya_inactivo"

    # Helper method for tests
    async def get_by_dni(self, service: AlumnoService, dni: str):
        """Helper to get alumno by DNI (not exposed in service)."""
        return await service.alumno_repo.get_by_dni(dni)

    # --- Pagination params validation ---

    def test_alumno_list_params_defaults(self):
        """Test AlumnoListParams defaults."""
        params = AlumnoListParams()
        assert params.limit == 20
        assert params.offset == 0
        assert params.activo is None
        assert params.search is None

    def test_alumno_list_params_validation(self):
        """Test AlumnoListParams validation."""
        with pytest.raises(ValidationError):
            AlumnoListParams(limit=0)
        with pytest.raises(ValidationError):
            AlumnoListParams(limit=101)
        with pytest.raises(ValidationError):
            AlumnoListParams(offset=-1)
