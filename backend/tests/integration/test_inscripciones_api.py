from httpx import AsyncClient


class TestInscripcionesAPI:
    """Integration tests for Inscripciones endpoints."""

    async def test_create_inscripcion_success(
        self, client: AsyncClient, auth_headers_admin, sample_alumno, sample_curso
    ):
        """Test successful inscripcion creation."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": sample_curso.id},
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["alumno_id"] == sample_alumno.id
        assert data["curso_id"] == sample_curso.id
        assert data["estado"] == "ACTIVA"

    async def test_create_inscripcion_curso_mismatch(
        self, client: AsyncClient, auth_headers_admin, sample_alumno, sample_curso
    ):
        """Test creating inscripcion with mismatched curso_id returns 400."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": 99999},
            headers=auth_headers_admin,
        )

        assert response.status_code == 400
        assert response.json()["code"] == "validacion_error"

    async def test_create_inscripcion_alumno_not_found(
        self, client: AsyncClient, auth_headers_admin, sample_curso
    ):
        """Test creating inscripcion for non-existent alumno returns 404."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            json={"alumno_id": 99999, "curso_id": sample_curso.id},
            headers=auth_headers_admin,
        )

        assert response.status_code == 404
        assert response.json()["code"] == "alumno_no_encontrado"

    async def test_create_inscripcion_curso_not_found(
        self, client: AsyncClient, auth_headers_admin, sample_alumno
    ):
        """Test creating inscripcion for non-existent curso returns 404."""
        response = await client.post(
            "/api/v1/cursos/99999/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": 99999},
            headers=auth_headers_admin,
        )

        assert response.status_code == 404

    async def test_create_inscripcion_duplicate_active_fails(
        self,
        client: AsyncClient,
        auth_headers_admin,
        sample_alumno,
        sample_curso,
        sample_inscripcion,
    ):
        """Test creating duplicate active inscripcion returns 409."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": sample_curso.id},
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "inscripcion_duplicada"

    async def test_create_inscripcion_cupo_lleno_fails(
        self, client: AsyncClient, auth_headers_admin, sample_curso
    ):
        """Test creating inscripcion when cupo is full returns 409."""
        # Create curso with cupos=1
        curso_resp = await client.post(
            "/api/v1/cursos",
            json={"nombre": "Cupo 1", "descripcion": "Test", "cupos": 1},
            headers=auth_headers_admin,
        )
        curso_id = curso_resp.json()["id"]

        # Create two alumnos
        alumno1 = await client.post(
            "/api/v1/alumnos",
            json={"dni": "11111111A", "nombre": "Uno", "apellido": "Test", "email": "uno@test.com"},
            headers=auth_headers_admin,
        )
        alumno2 = await client.post(
            "/api/v1/alumnos",
            json={"dni": "22222222B", "nombre": "Dos", "apellido": "Test", "email": "dos@test.com"},
            headers=auth_headers_admin,
        )

        # First inscripcion - OK
        await client.post(
            f"/api/v1/cursos/{curso_id}/inscripciones",
            json={"alumno_id": alumno1.json()["id"], "curso_id": curso_id},
            headers=auth_headers_admin,
        )

        # Second - should fail
        response = await client.post(
            f"/api/v1/cursos/{curso_id}/inscripciones",
            json={"alumno_id": alumno2.json()["id"], "curso_id": curso_id},
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "cupos_completos"

    async def test_list_inscripciones(
        self, client: AsyncClient, auth_headers_admin, sample_curso, sample_inscripcion
    ):
        """Test listing inscripciones for a curso."""
        response = await client.get(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["estado"] == "ACTIVA"

    async def test_list_inscripciones_filter_estado(
        self,
        client: AsyncClient,
        auth_headers_admin,
        sample_curso,
        sample_alumno,
        sample_inscripcion,
    ):
        """Test filtering inscripciones by estado."""
        # Create another alumno
        alumno2 = await client.post(
            "/api/v1/alumnos",
            json={"dni": "22222222B", "nombre": "Dos", "apellido": "Test", "email": "dos@test.com"},
            headers=auth_headers_admin,
        )

        await client.post(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            json={"alumno_id": alumno2.json()["id"], "curso_id": sample_curso.id},
            headers=auth_headers_admin,
        )

        # Baja one
        print(
            f"DEBUG: Deleting inscripcion for alumno_id={sample_alumno.id}, "
            f"curso_id={sample_curso.id}"
        )
        delete_resp = await client.delete(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones/{sample_alumno.id}",
            headers=auth_headers_admin,
        )
        print(f"DEBUG: Delete response: {delete_resp.status_code} - {delete_resp.json()}")

        response = await client.get(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones?estado=activa",
            headers=auth_headers_admin,
        )
        print(f"Filter activa response: {response.status_code} - {response.json()}")
        assert len(response.json()["items"]) == 1

        response = await client.get(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones?estado=baja",
            headers=auth_headers_admin,
        )
        print(f"Filter baja response: {response.status_code} - {response.json()}")
        assert len(response.json()["items"]) == 1

    async def test_delete_inscripcion_sets_baja(
        self, client: AsyncClient, auth_headers_admin, sample_curso, sample_inscripcion
    ):
        """Test deleting inscripcion sets estado to BAJA."""
        response = await client.delete(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones/{sample_inscripcion.alumno_id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "BAJA"

    async def test_delete_inscripcion_not_found(
        self, client: AsyncClient, auth_headers_admin, sample_curso
    ):
        """Test deleting non-existent inscripcion returns 404."""
        response = await client.delete(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones/99999",
            headers=auth_headers_admin,
        )

        assert response.status_code == 404

    async def test_docente_can_list_inscripciones(
        self,
        client: AsyncClient,
        auth_headers_admin,
        auth_headers_docente,
        docente_with_curso,
        sample_alumno,
    ):
        """Test docente can list inscripciones for their curso."""
        docente, curso = docente_with_curso

        # Create inscripcion
        await client.post(
            f"/api/v1/cursos/{curso.id}/inscripciones",
            json={"alumno_id": sample_alumno.id, "curso_id": curso.id},
            headers=auth_headers_admin,
        )

        # Docente should be able to list
        response = await client.get(
            f"/api/v1/cursos/{curso.id}/inscripciones",
            headers=auth_headers_docente,
        )

        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    async def test_docente_cannot_list_other_curso_inscripciones(
        self,
        client: AsyncClient,
        auth_headers_admin,
        auth_headers_docente,
        docente_user,
        sample_curso,
    ):
        """Test docente cannot list inscripciones for other curso (403)."""
        # Create a different curso that the docente is NOT assigned to
        other_curso = await client.post(
            "/api/v1/cursos",
            json={"nombre": "Otro Curso", "descripcion": "Otro", "cupos": 20},
            headers=auth_headers_admin,
        )
        other_curso_id = other_curso.json()["id"]

        # Docente should NOT be able to list inscripciones for other_curso
        response = await client.get(
            f"/api/v1/cursos/{other_curso_id}/inscripciones",
            headers=auth_headers_docente,
        )

        assert response.status_code == 403

    async def test_alumno_cannot_access_inscripciones(
        self, client: AsyncClient, auth_headers_alumno, sample_curso
    ):
        """Test alumno cannot access inscripciones endpoints (403)."""
        response = await client.get(
            f"/api/v1/cursos/{sample_curso.id}/inscripciones",
            headers=auth_headers_alumno,
        )
        assert response.status_code == 403


class TestAsignacionDocenteAPI:
    """Integration tests for Asignación Docente endpoints."""

    async def test_asignar_docente_success(
        self, client: AsyncClient, auth_headers_admin, docente_user, sample_curso
    ):
        """Test successful docente assignment."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/docentes?usuario_id={docente_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["curso_id"] == sample_curso.id
        assert data["usuario_id"] == docente_user.id

    async def test_asignar_docente_curso_not_found(
        self, client: AsyncClient, auth_headers_admin, docente_user
    ):
        """Test assigning docente to non-existent curso returns 404."""
        response = await client.post(
            f"/api/v1/cursos/99999/docentes?usuario_id={docente_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 404

    async def test_asignar_docente_usuario_not_found(
        self, client: AsyncClient, auth_headers_admin, sample_curso
    ):
        """Test assigning non-existent usuario returns 404."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/docentes?usuario_id=99999",
            headers=auth_headers_admin,
        )

        assert response.status_code == 404

    async def test_asignar_docente_usuario_not_docente_fails(
        self, client: AsyncClient, auth_headers_admin, admin_user, sample_curso
    ):
        """Test assigning non-docente user returns 409."""
        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/docentes?usuario_id={admin_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "usuario_no_es_docente"

    async def test_asignar_docente_duplicate_fails(
        self, client: AsyncClient, auth_headers_admin, docente_user, sample_curso
    ):
        """Test assigning same docente twice returns 409."""
        await client.post(
            f"/api/v1/cursos/{sample_curso.id}/docentes?usuario_id={docente_user.id}",
            headers=auth_headers_admin,
        )

        response = await client.post(
            f"/api/v1/cursos/{sample_curso.id}/docentes?usuario_id={docente_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 409
        assert response.json()["code"] == "docente_ya_asignado"

    async def test_desasignar_docente_success(
        self, client: AsyncClient, auth_headers_admin, docente_user, sample_curso
    ):
        """Test successful docente deassignment."""
        await client.post(
            f"/api/v1/cursos/{sample_curso.id}/docentes?usuario_id={docente_user.id}",
            headers=auth_headers_admin,
        )

        response = await client.delete(
            f"/api/v1/cursos/{sample_curso.id}/docentes/{docente_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        assert response.json()["code"] == "docente_desasignado"

    async def test_desasignar_docente_not_found(
        self, client: AsyncClient, auth_headers_admin, docente_user, sample_curso
    ):
        """Test deassigning non-existent assignment returns 404."""
        response = await client.delete(
            f"/api/v1/cursos/{sample_curso.id}/docentes/{docente_user.id}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 404
