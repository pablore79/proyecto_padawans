import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.models.usuario import RolUsuario
from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService
from tests.conftest import TEST_PASSWORD


class TestAuthService:
    """Unit tests for AuthService."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> AuthService:
        return AuthService(db_session)

    @pytest.fixture
    def admin_user_data(self) -> UserCreate:
        return UserCreate(
            username="testadmin",
            email="admin@test.com",
            password=TEST_PASSWORD,
            rol=RolUsuario.ADMIN,
        )

    @pytest.fixture
    def docente_user_data(self) -> UserCreate:
        return UserCreate(
            username="testdocente",
            email="docente@test.com",
            password=TEST_PASSWORD,
            rol=RolUsuario.DOCENTE,
        )

    @pytest.fixture
    def alumno_user_data(self, sample_alumno) -> UserCreate:
        return UserCreate(
            username="testalumno",
            email="alumno@test.com",
            password=TEST_PASSWORD,
            rol=RolUsuario.ALUMNO,
            alumno_id=sample_alumno.id,
        )

    # --- REGISTER tests ---

    async def test_register_admin_success(self, service: AuthService, admin_user_data: UserCreate):
        """Test successful admin user registration."""
        created = await service.register(admin_user_data, current_user_id=1)

        assert created.id is not None
        assert created.username == admin_user_data.username
        assert created.email == admin_user_data.email
        assert created.rol == RolUsuario.ADMIN
        assert created.alumno_id is None
        assert created.activo is True

    async def test_register_docente_success(
        self, service: AuthService, docente_user_data: UserCreate
    ):
        """Test successful docente user registration."""
        created = await service.register(docente_user_data, current_user_id=1)

        assert created.rol == RolUsuario.DOCENTE
        assert created.alumno_id is None

    async def test_register_alumno_success(
        self, service: AuthService, alumno_user_data: UserCreate
    ):
        """Test successful alumno user registration with alumno_id."""
        created = await service.register(alumno_user_data, current_user_id=1)

        assert created.rol == RolUsuario.ALUMNO
        assert created.alumno_id == alumno_user_data.alumno_id

    async def test_register_duplicate_username_fails(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test that duplicate username raises ConflictError."""
        await service.register(admin_user_data, current_user_id=1)

        duplicate = admin_user_data.model_copy(update={"email": "different@test.com"})
        with pytest.raises(ConflictError) as exc:
            await service.register(duplicate, current_user_id=1)

        assert exc.value.code == "usuario_duplicado"

    async def test_register_duplicate_email_fails(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test that duplicate email raises ConflictError."""
        await service.register(admin_user_data, current_user_id=1)

        duplicate = admin_user_data.model_copy(update={"username": "different"})
        with pytest.raises(ConflictError) as exc:
            await service.register(duplicate, current_user_id=1)

        assert exc.value.code == "usuario_duplicado"

    async def test_register_alumno_without_alumno_id_fails(self, service: AuthService):
        """Test that alumno without alumno_id raises UnauthorizedError."""
        data = UserCreate(
            username="testalumno",
            email="alumno@test.com",
            password="alumno123",
            rol=RolUsuario.ALUMNO,
            alumno_id=None,
        )
        with pytest.raises(UnauthorizedError) as exc:
            await service.register(data, current_user_id=1)

        assert exc.value.code == "rol_alumno_sin_alumno_id"

    async def test_register_admin_with_alumno_id_fails(self, service: AuthService, sample_alumno):
        """Test that admin with alumno_id raises UnauthorizedError."""
        data = UserCreate(
            username="testadmin2",
            email="admin2@test.com",
            password=TEST_PASSWORD,
            rol=RolUsuario.ADMIN,
            alumno_id=sample_alumno.id,
        )
        with pytest.raises(UnauthorizedError) as exc:
            await service.register(data, current_user_id=1)

        assert exc.value.code == "rol_admin_docente_con_alumno_id"

    async def test_register_docente_with_alumno_id_fails(self, service: AuthService, sample_alumno):
        """Test that docente with alumno_id raises UnauthorizedError."""
        data = UserCreate(
            username="testdocente2",
            email="docente2@test.com",
            password=TEST_PASSWORD,
            rol=RolUsuario.DOCENTE,
            alumno_id=sample_alumno.id,
        )
        with pytest.raises(UnauthorizedError) as exc:
            await service.register(data, current_user_id=1)

        assert exc.value.code == "rol_admin_docente_con_alumno_id"

    # --- LOGIN tests ---

    async def test_login_success(self, service: AuthService, admin_user_data: UserCreate):
        """Test successful login."""
        await service.register(admin_user_data, current_user_id=1)

        token = await service.login(admin_user_data.username, admin_user_data.password)

        assert token.access_token is not None
        assert token.token_type == "bearer"

    async def test_login_wrong_password_fails(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test login with wrong password raises UnauthorizedError."""
        await service.register(admin_user_data, current_user_id=1)

        with pytest.raises(UnauthorizedError) as exc:
            await service.login(admin_user_data.username, "wrongpassword")

        assert exc.value.code == "credenciales_invalidas"

    async def test_login_nonexistent_user_fails(self, service: AuthService):
        """Test login with non-existent user raises UnauthorizedError."""
        with pytest.raises(UnauthorizedError) as exc:
            await service.login("nonexistent", "password")

        assert exc.value.code == "credenciales_invalidas"

    async def test_login_inactive_user_fails(
        self, service: AuthService, db_session: AsyncSession, admin_user_data: UserCreate
    ):
        """Test login with inactive user raises UnauthorizedError."""
        user = await service.register(admin_user_data, current_user_id=1)
        # Deactivate user
        from sqlalchemy import select

        from app.models.usuario import Usuario

        result = await db_session.execute(select(Usuario).where(Usuario.id == user.id))
        db_user = result.scalar_one()
        db_user.activo = False
        await db_session.flush()

        with pytest.raises(UnauthorizedError) as exc:
            await service.login(admin_user_data.username, admin_user_data.password)

        assert exc.value.code == "credenciales_invalidas"

    # --- GET_CURRENT_USER tests ---

    async def test_get_current_user_valid_token(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test getting user from valid token."""
        await service.register(admin_user_data, current_user_id=1)
        token = await service.login(admin_user_data.username, admin_user_data.password)

        user = await service.get_current_user(token.access_token)

        assert user.id is not None
        assert user.username == admin_user_data.username

    async def test_get_current_user_invalid_token(self, service: AuthService):
        """Test getting user with invalid token raises UnauthorizedError."""
        with pytest.raises(UnauthorizedError) as exc:
            await service.get_current_user("invalid.token.here")

        assert exc.value.code == "token_invalido"

    async def test_get_current_user_expired_token(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test getting user with expired token raises UnauthorizedError."""
        # Create token with very short expiry
        from datetime import timedelta

        from app.core.security import create_access_token, create_token_data

        await service.register(admin_user_data, current_user_id=1)
        token_data = create_token_data(user_id=1, username="test", rol="admin", alumno_id=None)
        expired_token = create_access_token(token_data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(UnauthorizedError) as exc:
            await service.get_current_user(expired_token)

        assert exc.value.code == "token_invalido"

    async def test_get_current_user_nonexistent_user(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test getting user for non-existent user raises UnauthorizedError."""
        await service.register(admin_user_data, current_user_id=1)
        token = await service.login(admin_user_data.username, admin_user_data.password)
        # Delete user from DB
        from sqlalchemy import delete

        from app.models.usuario import Usuario

        await service.db.execute(
            delete(Usuario).where(Usuario.username == admin_user_data.username)
        )
        await service.db.flush()

        with pytest.raises(UnauthorizedError) as exc:
            await service.get_current_user(token.access_token)

        assert exc.value.code == "token_invalido"

    # --- VALIDATE_ROLE tests ---

    async def test_validate_role_admin_allowed(
        self, service: AuthService, admin_user_data: UserCreate
    ):
        """Test admin role validation passes for admin."""
        await service.register(admin_user_data, current_user_id=1)
        user = await service.usuario_repo.get_by_username(admin_user_data.username)
        await service.validate_role(user, ["admin"])

    async def test_validate_role_admin_forbidden_for_docente(
        self, service: AuthService, docente_user_data: UserCreate
    ):
        """Test admin role validation fails for docente."""
        await service.register(docente_user_data, current_user_id=1)
        user = await service.usuario_repo.get_by_username(docente_user_data.username)

        with pytest.raises(Exception) as exc:
            await service.validate_role(user, ["admin"])

        assert exc.value.code == "sin_permisos"
