from httpx import AsyncClient


class TestAlumnosAPI:
    """Integration tests for Alumnos endpoints."""

    async def test_list_alumnos_empty(self, client: AsyncClient, auth_headers_admin):
        """Test listing alumnos when empty."""
        response = await client.get("/api/v1/alumnos", headers=auth_headers_admin)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_create_alumno_success(self, client: AsyncClient, auth_headers_admin):
        """Test successful alumno creation."""
        response = await client.post(
            "/api/v1/alumnos",
            json={
                "dni": "11111111A",
                "nombre": "Nuevo",
                "apellido": "Alumno",
                "email": "nuevo@test.com",
                "telefono": "123456789",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["dni"] == "11111111A"
        assert data["nombre"] == "Nuevo"
        assert data["activo"] is True

    async def test_create_alumno_duplicate_dni(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test creating alumno with duplicate DNI returns 409."""
        response = await client.post(
            "/api/v1/alumnos",
            json={
                "dni": sample_alumno.dni,
                "nombre": "Otro",
                "apellido": "Alumno",
                "email": "otro@test.com",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "dni_duplicado"

    async def test_create_alumno_duplicate_email(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test creating alumno with duplicate email returns 409."""
        response = await client.post(
            "/api/v1/alumnos",
            json={
                "dni": "22222222B",
                "nombre": "Otro",
                "apellido": "Alumno",
                "email": sample_alumno.email,
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "email_duplicado"

    async def test_create_alumno_validation_error(self, client: AsyncClient, auth_headers_admin):
        """Test creating alumno with invalid data returns 422."""
        response = await client.post(
            "/api/v1/alumnos",
            json={
                "dni": "invalid",
                "nombre": "",
                "apellido": "Alumno",
                "email": "not-an-email",
            },
            headers=auth_headers_admin,
        )

        assert response.status_code == 422
        assert response.json()["code"] == "validacion_error"

    async def test_get_alumno_success(self, client: AsyncClient, auth_headers_admin, sample_alumno):
        """Test getting alumno by ID."""
        response = await client.get(
            f"/api/v1/alumnos/{sample_alumno.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_alumno.id
        assert data["dni"] == sample_alumno.dni

    async def test_get_alumno_not_found(self, client: AsyncClient, auth_headers_admin):
        """Test getting non-existent alumno returns 404."""
        response = await client.get("/api/v1/alumnos/99999", headers=auth_headers_admin)

        assert response.status_code == 404
        assert response.json()["code"] == "alumno_no_encontrado"

    async def test_update_alumno_success(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test updating alumno."""
        response = await client.patch(
            f"/api/v1/alumnos/{sample_alumno.id}",
            json={"nombre": "Actualizado", "telefono": "999999999"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Actualizado"
        assert data["telefono"] == "999999999"

    async def test_update_alumno_duplicate_dni(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test updating alumno to duplicate DNI returns 409."""
        # Create another alumno first
        await client.post(
            "/api/v1/alumnos",
            json={
                "dni": "22222222B",
                "nombre": "Otro",
                "apellido": "Alumno",
                "email": "otro@test.com",
            },
            headers=auth_headers_admin,
        )

        response = await client.patch(
            f"/api/v1/alumnos/{sample_alumno.id}",
            json={"dni": "22222222B"},
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "dni_duplicado"

    async def test_delete_alumno_soft_delete(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test soft deleting alumno."""
        response = await client.delete(
            f"/api/v1/alumnos/{sample_alumno.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is False

        # Verify it's not in active list
        list_resp = await client.get("/api/v1/alumnos?activo=true", headers=auth_headers_admin)
        assert len(list_resp.json()["items"]) == 0

    async def test_delete_alumno_not_found(self, client: AsyncClient, auth_headers_admin):
        """Test deleting non-existent alumno returns 404."""
        response = await client.delete("/api/v1/alumnos/99999", headers=auth_headers_admin)

        assert response.status_code == 404

    async def test_reactivar_alumno(self, client: AsyncClient, auth_headers_admin, sample_alumno):
        """Test reactivating a soft-deleted alumno."""
        await client.delete(f"/api/v1/alumnos/{sample_alumno.id}", headers=auth_headers_admin)

        response = await client.post(
            f"/api/v1/alumnos/{sample_alumno.id}/reactivar", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["activo"] is True

    async def test_reactivar_alumno_already_active_fails(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test reactivating already active alumno returns 409."""
        response = await client.post(
            f"/api/v1/alumnos/{sample_alumno.id}/reactivar", headers=auth_headers_admin
        )

        assert response.status_code == 409
        assert response.json()["code"] == "alumno_ya_activo"

    async def test_list_alumnos_filter_activo(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test filtering alumnos by activo."""
        response = await client.get("/api/v1/alumnos?activo=true", headers=auth_headers_admin)
        assert len(response.json()["items"]) == 1

        await client.delete(f"/api/v1/alumnos/{sample_alumno.id}", headers=auth_headers_admin)

        response = await client.get("/api/v1/alumnos?activo=true", headers=auth_headers_admin)
        assert len(response.json()["items"]) == 0

        response = await client.get("/api/v1/alumnos?activo=false", headers=auth_headers_admin)
        assert len(response.json()["items"]) == 1

    async def test_list_alumnos_search(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test searching alumnos by DNI/nombre/apellido."""
        response = await client.get(
            f"/api/v1/alumnos?search={sample_alumno.nombre[:3]}", headers=auth_headers_admin
        )
        assert len(response.json()["items"]) == 1

        response = await client.get(
            f"/api/v1/alumnos?search={sample_alumno.dni[:3]}", headers=auth_headers_admin
        )
        assert len(response.json()["items"]) == 1

    async def test_list_alumnos_pagination(self, client: AsyncClient, auth_headers_admin):
        """Test pagination."""
        for i in range(5):
            await client.post(
                "/api/v1/alumnos",
                json={
                    "dni": f"{i}1111111A",
                    "nombre": f"Alumno{i}",
                    "apellido": "Test",
                    "email": f"test{i}@test.com",
                },
                headers=auth_headers_admin,
            )

        response = await client.get("/api/v1/alumnos?limit=2&offset=0", headers=auth_headers_admin)
        assert len(response.json()["items"]) == 2

        response = await client.get("/api/v1/alumnos?limit=2&offset=2", headers=auth_headers_admin)
        assert len(response.json()["items"]) == 2

    async def test_docente_cannot_access_alumnos(self, client: AsyncClient, auth_headers_docente):
        """Test docente cannot access alumnos endpoints (403)."""
        response = await client.get("/api/v1/alumnos", headers=auth_headers_docente)
        assert response.status_code == 403

    async def test_alumno_cannot_access_alumnos(self, client: AsyncClient, auth_headers_alumno):
        """Test alumno cannot access alumnos endpoints (403)."""
        response = await client.get("/api/v1/alumnos", headers=auth_headers_alumno)
        assert response.status_code == 403
