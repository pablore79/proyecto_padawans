from httpx import AsyncClient

from tests.conftest import TEST_PASSWORD


class TestAuthAPI:
    """Integration tests for Auth endpoints."""

    async def test_login_success(self, client: AsyncClient, admin_user):
        """Test successful login returns token."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": admin_user.username, "password": TEST_PASSWORD},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, admin_user):
        """Test login with wrong password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": admin_user.username, "password": "wrong"},
        )

        assert response.status_code == 401
        assert response.json()["code"] == "credenciales_invalidas"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )

        assert response.status_code == 401

    async def test_me_with_valid_token(self, client: AsyncClient, auth_headers_admin, admin_user):
        """Test /me endpoint with valid token."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == admin_user.username
        assert data["email"] == admin_user.email
        assert data["rol"] == "admin"

    async def test_me_without_token(self, client: AsyncClient):
        """Test /me without token returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert response.json()["code"] == "token_invalido"

    async def test_me_with_invalid_token(self, client: AsyncClient):
        """Test /me with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token"}
        )

        assert response.status_code == 401

    async def test_create_user_admin_only(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test admin can create users."""
        response = await client.post(
            "/api/v1/auth/users",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": TEST_PASSWORD,
                "rol": "docente",
            },
            headers=auth_headers_admin,
        )
        print(f"Response: {response.status_code} - {response.json()}")
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["rol"] == "docente"

    async def test_create_user_docente_forbidden(self, client: AsyncClient, auth_headers_docente):
        """Test docente cannot create users (403)."""
        response = await client.post(
            "/api/v1/auth/users",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": TEST_PASSWORD,
                "rol": "alumno",
            },
            headers=auth_headers_docente,
        )

        assert response.status_code == 403

    async def test_create_user_alumno_forbidden(self, client: AsyncClient, auth_headers_alumno):
        """Test alumno cannot create users (403)."""
        response = await client.post(
            "/api/v1/auth/users",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": TEST_PASSWORD,
                "rol": "admin",
            },
            headers=auth_headers_alumno,
        )

        assert response.status_code == 403

    async def test_create_user_duplicate_username(
        self, client: AsyncClient, auth_headers_admin, admin_user
    ):
        """Test creating user with duplicate username returns 409."""
        response = await client.post(
            "/api/v1/auth/users",
            json={
                "username": admin_user.username,
                "email": "different@test.com",
                "password": TEST_PASSWORD,
                "rol": "docente",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "usuario_duplicado"

    async def test_create_alumno_user_requires_alumno_id(
        self, client: AsyncClient, auth_headers_admin
    ):
        """Test creating alumno user without alumno_id returns 401."""
        response = await client.post(
            "/api/v1/auth/users",
            json={
                "username": "newalumno",
                "email": "newalumno@test.com",
                "password": TEST_PASSWORD,
                "rol": "alumno",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 401
        assert response.json()["code"] == "rol_alumno_sin_alumno_id"

    async def test_create_admin_user_with_alumno_id_fails(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test creating admin user with alumno_id returns 401."""
        response = await client.post(
            "/api/v1/auth/users",
            json={
                "username": "newadmin",
                "email": "newadmin@test.com",
                "password": TEST_PASSWORD,
                "rol": "admin",
                "alumno_id": sample_alumno.id,
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 401
        assert response.json()["code"] == "rol_admin_docente_con_alumno_id"
