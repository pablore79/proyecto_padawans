# PRD - Sistema de Administración de Alumnos

**Proyecto:** proyecto_padawans
**Cliente interno:** Bunker4 (jornada formativa)
**Versión:** 0.1.0 (inicial)
**Estado:** Borrador

---

## 1. Resumen

Sistema web para administrar alumnos de Bunker4: alta/baja/modificación de alumnos, gestión de cursos y materias, y autenticación por roles (admin, docente, alumno). Backend en FastAPI + SQLAlchemy sobre PostgreSQL. No incluye frontend dedicado en este alcance; se expone vía API REST documentada con OpenAPI.

## 2. Problema

Bunker4 actualmente administra su lista de alumnos, los cursos en los que están inscriptos y quién queda a cargo de cada curso de forma manual (planillas, docs sueltos). Esto produce:

- Duplicados de alumnos.
- Reportes inconsistentes.
- Sin control de acceso: cualquiera con la planilla edita.
- Dificultad para seguir cuántos alumnos hay por curso.

## 3. Objetivos

- Centralizar la administración de alumnos y cursos en un único servicio.
- Garantizar que cada operación quede registrada con quién y cuándo.
- Permitir que tres roles distintos (admin, docente, alumno) accedan a funciones acotadas a su rol.
- Asegurar que la base no quede inconsistente (inscripciones inválidas, cursos huérfanos).

## 4. No objetivos (este alcance)

- Frontend web/mobile dedicado.
- Gestión de calificaciones/notas.
- Gestión de asistencia.
- Reportes y dashboard.
- Integraciones externas (Google Sheets, mail, etc.).
- Multi-tenant.

## 5. Personas y roles

| Rol | Descripción | Acciones permitidas |
|-----|-------------|---------------------|
| **admin** | Coordinador de Bunker4. | CRUD alumnos, CRUD cursos/materias, CRUD docentes, asignar docentes a cursos, inscribir alumnos en cursos. |
| **docente** | Responsable de uno o varios cursos. | Ver listado de alumnos de sus cursos, ver su propio perfil. NO puede crear alumnos ni cursos. |
| **alumno** | persona cursando. | Ver su propio perfil, ver los cursos en los que está inscripto. No puede editar nada. |

## 6. Entidades

### 6.1 Alumno

- `id` (int, PK)
- `dni` (string, único, validado)
- `nombre` (string)
- `apellido` (string)
- `email` (string, único, validado)
- `telefono` (string, opcional)
- `fecha_nacimiento` (date, opcional)
- `usuario_github` (string, opcional) — username de GitHub
- `usuario_gitlab` (string, opcional) — username de GitLab
- `perfil_linkedin` (string, opcional) — URL del perfil de LinkedIn
- `activo` (bool, default `true`) — soft delete
- `created_at`, `updated_at`, `created_by`, `updated_by`

### 6.2 Curso

- `id` (int, PK)
- `nombre` (string, único)
- `descripcion` (string, opcional)
- `cupos` (int, default 20)
- `activo` (bool, default `true`)
- `created_at`, `updated_at`, `created_by`, `updated_by`

### 6.3 Materia

> Nota de alcance: "materias" se modela como unidades dentro de un curso. En este alcance inicial se tratan como entidades simples asociadas a un curso.

- `id` (int, PK)
- `curso_id` (FK → Curso)
- `nombre` (string)
- `descripcion` (string, opcional)
- `created_at`, `updated_at`

### 6.4 Inscripción (relación alumno ↔ curso)

- `id` (int, PK)
- `alumno_id` (FK → Alumno)
- `curso_id` (FK → Curso)
- `fecha_inscripcion` (timestamp, default now)
- `estado` (enum: `activa`, `baja`)
- Unique constraint `(alumno_id, curso_id)` con validación de `estado=activa` única.

### 6.5 Asignación docente (relación usuario ↔ curso)

- `id` (int, PK)
- `usuario_id` (FK → Usuario, rol docente)
- `curso_id` (FK → Curso)
- Unique constraint `(usuario_id, curso_id)`

### 6.6 Usuario

- `id` (int, PK)
- `username` (string, único)
- `email` (string, único)
- `password_hash` (string)
- `rol` (enum: `admin`, `docente`, `alumno`)
- `alumno_id` (FK → Alumno, opcional, solo si rol=alumno)
- `activo` (bool, default `true`)
- `created_at`, `updated_at`, `created_by`

## 7. Reglas de negocio

1. No se puede crear dos alumnos con el mismo `dni` ni el mismo `email`.
2. No se puede inscribir a un alumno ya `activo` en un curso en el que ya tiene `estado=activa`.
3. La capacidad (`cupos`) del curso no se debe exceder con inscripciones `activa`. Validar antes de insertar y rechazar con 409.
4. Al dar de baja un alumno (`activo=false`), todas sus inscripciones `activa` pasan a `estado=baja`.
5. Al dar de baja un curso (`activo=false`), todas sus inscripciones `activa` pasan a `estado=baja` y se des-asignan los docentes.
6. Un usuario con `rol=alumno` debe tener `alumno_id` no nulo. Un usuario con `rol=admin` o `rol=docente` debe tener `alumno_id` nulo.
7. `created_by` = id del usuario que ejecutó el alta. `updated_by` = id del usuario que ejecutó la última modificación.
8. El soft delete (`activo=false`) NO borra filas. Solo los procesos de mantenimiento de base (fuera del alcance de esta API) pueden hacer hard delete.

## 8. Endpoints (alto nivel)

### Autenticación

- `POST /auth/login` → `{ access_token, token_type: "bearer" }`
- `GET /auth/me` → usuario actual

### Alumnos (admin)

- `GET /alumnos` (con filtros: activo, búsqueda por dni/nombre; paginación)
- `POST /alumnos`
- `GET /alumnos/{id}`
- `PATCH /alumnos/{id}`
- `DELETE /alumnos/{id}` (soft delete: `activo=false`)

### Cursos (admin)

- `GET /cursos`
- `POST /cursos`
- `GET /cursos/{id}`
- `PATCH /cursos/{id}`
- `DELETE /cursos/{id}` (soft delete)

### Materias (admin)

- `GET /cursos/{curso_id}/materias`
- `POST /cursos/{curso_id}/materias`
- `PATCH /materias/{id}`
- `DELETE /materias/{id}`

### Inscripciones

- `POST /cursos/{curso_id}/inscripciones` (body: `alumno_id`) — admin
- `DELETE /cursos/{curso_id}/inscripciones/{alumno_id}` — admin (estado=baja)
- `GET /cursos/{curso_id}/inscripciones` — admin + docente del curso

### Asignación docente (admin)

- `POST /cursos/{curso_id}/docentes` (body: `usuario_id`)
- `DELETE /cursos/{curso_id}/docentes/{usuario_id}`

### Vistas por rol

- `GET /docente/me/cursos` (docente) → cursos del docente logueado + alumnos de cada uno
- `GET /alumno/me/cursos` (alumno) → cursos con inscripción activa del alumno logueado

## 9. Casos de uso clave

### UC-1: Alta de alumno

**Actor:** admin
**Flujo:**
1. Admin hace POST `/auth/login` con credenciales admin.
2. Admin hace POST `/alumnos` con datos del alumno.
3. Sistema valida dni y email únicos.
4. Sistema crea alumno con `created_by` = id del admin.
5. Sistema devuelve 201 con el alumno creado.

**Errores:** 400 (validación), 409 (dni/email duplicado).

### UC-2: Inscripción con cupo lleno

**Actor:** admin
**Flujo:**
1. Admin hace POST `/cursos/{curso_id}/inscripciones`.
2. Sistema verifica que la cantidad de inscripciones `activa` < `cupos`.
3. Si alcanza el cupo, devuelve 409 con mensaje `cupos_completos`.
4. Si hay cupo, crea inscripción con `estado=activa`.

**Errores:** 409 `cupos_completos`, 404 `curso_no_encontrado`

### UC-3: Docente ve sus cursos y alumnos

**Actor:** docente
**Flujo:**
1. Docente hace POST `/auth/login`.
2. Docente hace GET `/docente/me/cursos`.
3. Sistema filtra cursos donde `asignacion_docente.usuario_id` = su id.
4. Para cada curso, incluye listado de alumnos con inscripción `activa`.

### UC-4: Alumno consulta sus cursos

**Actor:** alumno
**Flujo:**
1. Alumno hace POST `/auth/login`.
2. Alumno hace GET `/alumno/me/cursos`.
3. Sistema filtra por su `alumno_id` y `estado=activa`.

## 10. Requisitos no funcionales

- **Autenticación**: JWT. `access_token` con expiración 60 minutos. Algoritmo HS256.
- **Contraseñas**: bcrypt. Nunca se devuelve `password_hash`.
- **Auditoría**: todas las mutations registran `created_by` / `updated_by`.
- **Logging**: incluir `request_id` (UUID por request) en logs.
- **Errores**: formato uniforme `{ "detail": "...", "code": "..." }`. Códigos estables para que el frontend pueda mapear.
- **Versiónado**: API versionada con prefijo `/api/v1` (decisión final en PLAN.md).
- **Internacionalización API**: mensajes de error en español neutro por defecto.
- **DB**: UTF-8, timezone UTC en timestamps.
- **Paginación**: listados con `limit` (default 20, max 100) y `offset`.

## 11. Supuestos

1. No existen alumnos menores sin email propio; el `email` es obligatorio para cada alumno.
2. Cada alumno tiene un único `dni`.
3. Un curso puede tener varios docentes asignados (relación many-to-many).
4. No hay requisitos deconcurrencia alta; el scope es una sola sede de Bunker4.

## 12. Riesgos

| Riesgo | Mitigación |
|--------|-----------|
| Conflicto de versiones entre SQLAlchemy 2.0 y snippets viejos de tutorial | Empezar con SQLAlchemy 2.0 sync style然后再 migrar a async; no copiar tutoriales de 1.4. |
| `asyncpg` vs `psycopg` para async DB | Decisión final en PLAN.md; se elige `psycopg[binary]` con soporte async nativo en Python 3.12. |
| Postgres local vs Docker | Se recomienda Docker; se documenta alternativa en README. |
| Hard delete accidental | Regla de negocio 8: soft delete únicamente. |

## 13. Criterios de aceptación (primer slice)

1. Un admin puede crear, listar, modificar y dar de baja alumnos.
2. Un admin puede crear cursos y materias dentro de cursos.
3. Un admin puede inscribir alumnos en cursos respetando cupos.
4. Un docente puede loguearse y ver sus cursos y alumnos.
5. Un alumno puede loguearse y ver sus cursos activos.
6. Todas las mutations registran `created_by` / `updated_by`.
7. No se puede inscribir a un alumno en un curso lleno (409).
8. Soft delete propaga baja a inscripciones (reglas 4 y 5).
9. Endpoints de OpenAPI `/docs` funcionando.
10. Test suite (cuando exista) pasa con al menos los casos de UC-1 a UC-4.

## 14. Fuera de scope (explicito)

- Calificaciones / notas.
- Asistencia.
- Reportes / dashboard.
- Frontend.
- Notificaciones por email.
- Backup automático (es responsabilidad de ops con Docker postgres volumes).

---

**Próximo paso:** [PLAN.md](./PLAN.md) traduce este PRD en decisiones técnicas y plan de implementación.
