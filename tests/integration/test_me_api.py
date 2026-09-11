from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import TEST_PASSWORD


class TestDocenteMeAPI:
    """Integration tests for Docente /me endpoints."""

    async def test_me_cursos_empty(self, client: AsyncClient, auth_headers_docente):
        """Test docente with no assigned cursos gets empty list."""
        response = await client.get("/api/v1/docente/me/cursos", headers=auth_headers_docente)

        assert response.status_code == 200
        data = response.json()
        assert data["docente_id"] is not None
        assert data["cursos"] == []

    async def test_me_cursos_with_data(
        self,
        client: AsyncClient,
        auth_headers_admin,
        auth_headers_docente,
        docente_with_curso,
        sample_alumno,
    ):
        """Test docente gets their cursos with alumnos."""
        docente, curso = docente_with_curso

        # Create inscripcion
        await client.post(
            f"/api/v1/cursos/{curso.id}/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": curso.id},
            headers=auth_headers_admin,
        )

        response = await client.get("/api/v1/docente/me/cursos", headers=auth_headers_docente)

        assert response.status_code == 200
        data = response.json()
        assert len(data["cursos"]) == 1
        assert data["cursos"][0]["id"] == curso.id
        assert len(data["cursos"][0]["alumnos"]) == 1
        assert data["cursos"][0]["alumnos"][0]["id"] == sample_alumno.id

    async def test_me_cursos_only_active_cursos(
        self,
        client: AsyncClient,
        auth_headers_admin,
        auth_headers_docente,
        docente_user,
        db_session,
    ):
        """Test docente only sees active cursos."""
        from app.models.curso import Curso

        # Create inactive curso
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

        await client.post(
            f"/api/v1/cursos/{curso_inactivo.id}/docentes?usuario_id={docente_user.id}",
            headers=auth_headers_admin,
        )

        response = await client.get("/api/v1/docente/me/cursos", headers=auth_headers_docente)

        assert response.status_code == 200
        data = response.json()
        assert len(data["cursos"]) == 0

    async def test_me_cursos_only_active_inscripciones(
        self,
        client: AsyncClient,
        auth_headers_admin,
        auth_headers_docente,
        docente_with_curso,
        sample_alumno,
    ):
        """Test docente only sees active inscripciones."""
        docente, curso = docente_with_curso

        # Create inscripcion and then baja it
        await client.post(
            f"/api/v1/cursos/{curso.id}/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": curso.id},
            headers=auth_headers_admin,
        )

        await client.delete(
            f"/api/v1/cursos/{curso.id}/inscripciones/{sample_alumno.id}",
            headers=auth_headers_admin,
        )

        response = await client.get("/api/v1/docente/me/cursos", headers=auth_headers_docente)

        assert response.status_code == 200
        data = response.json()
        assert len(data["cursos"][0]["alumnos"]) == 0

    async def test_admin_cannot_access_docente_me(self, client: AsyncClient, auth_headers_admin):
        """Test admin cannot access docente/me endpoints (403)."""
        response = await client.get("/api/v1/docente/me/cursos", headers=auth_headers_admin)
        assert response.status_code == 403

    async def test_alumno_cannot_access_docente_me(self, client: AsyncClient, auth_headers_alumno):
        """Test alumno cannot access docente/me endpoints (403)."""
        response = await client.get("/api/v1/docente/me/cursos", headers=auth_headers_alumno)
        assert response.status_code == 403


class TestAlumnoMeAPI:
    """Integration tests for Alumno /me endpoints."""

    async def test_me_cursos_empty(self, client: AsyncClient, auth_headers_alumno):
        """Test alumno with no inscripciones gets empty list."""
        response = await client.get("/api/v1/alumno/me/cursos", headers=auth_headers_alumno)

        assert response.status_code == 200
        data = response.json()
        assert data["alumno_id"] is not None
        assert data["cursos"] == []

    async def test_me_cursos_with_data(
        self, client: AsyncClient, auth_headers_alumno, alumno_with_inscripcion
    ):
        """Test alumno gets their cursos with active inscripciones."""
        user, alumno, curso = alumno_with_inscripcion

        response = await client.get("/api/v1/alumno/me/cursos", headers=auth_headers_alumno)

        assert response.status_code == 200
        data = response.json()
        assert len(data["cursos"]) == 1
        assert data["cursos"][0]["id"] == curso.id
        assert "fecha_inscripcion" in data["cursos"][0]

    async def test_me_cursos_only_active_inscripciones(
        self, client: AsyncClient, auth_headers_admin, auth_headers_alumno, alumno_with_inscripcion
    ):
        """Test alumno only sees active inscripciones."""
        user, alumno, curso = alumno_with_inscripcion

        # Baja the inscripcion
        await client.delete(
            f"/api/v1/cursos/{curso.id}/inscripciones/{alumno.id}",
            headers=auth_headers_admin,
        )

        response = await client.get("/api/v1/alumno/me/cursos", headers=auth_headers_alumno)

        assert response.status_code == 200
        data = response.json()
        assert len(data["cursos"]) == 0

    async def test_me_cursos_only_active_cursos(
        self, client: AsyncClient, auth_headers_admin, auth_headers_alumno, alumno_user, db_session
    ):
        """Test alumno only sees active cursos."""
        from app.models.curso import Curso

        user, alumno = alumno_user

        # Create inactive curso
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

        # Create inscripcion
        await client.post(
            f"/api/v1/cursos/{curso_inactivo.id}/inscripciones",
            json={"alumno_id": alumno.id, "curso_id": curso_inactivo.id},
            headers=auth_headers_admin,
        )

        response = await client.get("/api/v1/alumno/me/cursos", headers=auth_headers_alumno)

        assert response.status_code == 200
        data = response.json()
        assert len(data["cursos"]) == 0

    async def test_alumno_without_alumno_id_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test alumno user without alumno_id gets 401."""
        # Create alumno user without linked alumno
        from app.core.security import get_password_hash
        from app.models.usuario import RolUsuario, Usuario

        usuario = Usuario(
            username="orphan_alumno",
            email="orphan@test.com",
            password_hash=get_password_hash(TEST_PASSWORD),
            rol=RolUsuario.ALUMNO,
            alumno_id=None,
            activo=True,
        )
        db_session.add(usuario)
        await db_session.flush()
        await db_session.refresh(usuario)

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "orphan_alumno", "password": TEST_PASSWORD},
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/alumno/me/cursos", headers=headers)
        assert response.status_code == 401
        assert response.json()["code"] == "rol_alumno_sin_alumno_id"

    async def test_admin_cannot_access_alumno_me(self, client: AsyncClient, auth_headers_admin):
        """Test admin cannot access alumno/me endpoints (403)."""
        response = await client.get("/api/v1/alumno/me/cursos", headers=auth_headers_admin)
        assert response.status_code == 403

    async def test_docente_cannot_access_alumno_me(self, client: AsyncClient, auth_headers_docente):
        """Test docente cannot access alumno/me endpoints (403)."""
        response = await client.get("/api/v1/alumno/me/cursos", headers=auth_headers_docente)
        assert response.status_code == 403
