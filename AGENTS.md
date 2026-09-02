# AGENTS.md — Instrucciones para Agentes de IA

**Proyecto:** proyecto_padawans
**Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x async, PostgreSQL 16, pytest
**Documentación base:** [PRD.md](./PRD.md), [PLAN.md](./PLAN.md), [README.md](./README.md)

---

## 1. Contexto de Trabajo

Este repositorio implementa un **sistema de administración de alumnos** para Bunker4 (jornada formativa). Es un backend **API REST** sin frontend dedicado. La interfaz es OpenAPI/Swagger en `/docs`.

**Arquitectura:** Clean/Hexagonal simplificada
- `app/api/v1/` → Routers (adaptadores de entrada)
- `app/services/` → Casos de uso / reglas de negocio
- `app/repositories/` → Acceso a datos (SQLAlchemy)
- `app/models/` → Entidades ORM
- `app/schemas/` → DTOs Pydantic (request/response)
- `app/core/` → Config, seguridad, DB, excepciones

---

## 2. Environment Obligatorio

**Antes de CUALQUIER comando** (tests, uvicorn, alembic, pip, ruff, mypy):

```bash
conda activate py3.12
```

La creación del environment (`conda create -n py3.12 python=3.12`) se hace **una sola vez por máquina**. Ver [README.md](./README.md#activación-del-environment-en-cada-arranque-importante).

---

## 3. Convenciones de Código

### Estilo y Calidad
- **Lint/Format:** `ruff` (config en `pyproject.toml`). Ejecutar antes de commit:
  ```bash
  ruff check . && ruff format .
  ```
- **Type checking:** `mypy --strict app/` (sin ignores salvo justificación documentada)
- **Imports:** absolutos desde `app.` (ej: `from app.models.alumno import Alumno`)
- **Async por defecto:** FastAPI + SQLAlchemy async → handlers `async def`, repos `async`, services `async`
- **Sin `print()`** en código de producción. Usar `logging` con `request_id`

### Patrones Obligatorios
| Patrón | Regla |
|--------|-------|
| **Repository** | Un archivo por entidad en `app/repositories/`. Métodos: `get`, `list`, `create`, `update`, `delete`, `exists` |
| **Service** | Un archivo por dominio en `app/services/`. Contiene **todas** las reglas de negocio. Los routers **no** tienen lógica de negocio |
| **Dependency Injection** | `get_db` (session), `get_current_user`, `require_role(*roles)` en `app/api/deps.py` |
| **Errores** | Excepciones custom en `app/core/exceptions.py` → handlers registrados en `main.py`. Formato: `{ "detail": "...", "code": "..." }` |
| **Auditoría** | Toda mutation setea `created_by` / `updated_by` = `current_user.id` |
| **Soft Delete** | Campo `activo: bool`. `DELETE` = `activo=False`. Repos filtran `activo=True` por defecto |

### Nomenclatura
| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Archivos/módulos | `snake_case` | `alumno_service.py` |
| Clases/Modelos | `PascalCase` | `Alumno`, `AlumnoCreate` |
| Funciones/vars | `snake_case` | `get_alumno_by_dni` |
| Constantes | `UPPER_SNAKE` | `DEFAULT_PAGE_SIZE` |
| Tablas DB | `snake_case` plural | `alumnos`, `inscripciones` |
| Columnas DB | `snake_case` | `fecha_nacimiento` |
| Enums Python | `str, Enum` | `class EstadoInscripcion(str, Enum)` |
| Error codes | `snake_case` | `dni_duplicado`, `cupos_completos` |

---

## 4. Flujo de Trabajo Estándar

### Para implementar una feature / fix:
1. **Leer** PRD.md (reglas de negocio) y PLAN.md (fase actual)
2. **Escribir test primero** (TDD): unitario en `tests/unit/`, integración en `tests/integration/`
3. **Implementar** en orden: schema → repository → service → router
4. **Verificar local:**
   ```bash
   ruff check . && ruff format . && mypy --strict app/
   pytest -x -q
   ```
5. **Migración** si hay cambio de modelo:
   ```bash
   alembic revision --autogenerate -m "descripcion_corta"
   alembic upgrade head
   ```
6. **Commit** con mensaje convencional:
   ```
   feat(alumnos): agregar filtro por dni en listado
   fix(inscripciones): validar cupo antes de crear (409)
   ```

### Para crear un endpoint nuevo:
1. Schema request/response en `app/schemas/<dominio>.py`
2. Método en repository (`app/repositories/<entidad>_repo.py`)
3. Lógica en service (`app/services/<dominio>_service.py`)
4. Router en `app/api/v1/<recurso>.py`
5. Registrar router en `app/api/v1/router.py`
6. Tests: unit (service) + integración (router)

---

## 5. Reglas de Negocio Inmutables (del PRD)

**NO violar estas reglas bajo ningún pretexto:**

1. **Unicidad:** `dni` y `email` de alumno son únicos (regla 1)
2. **Inscripción duplicada:** No inscribir alumno ya `activo` en mismo curso (regla 2)
3. **Cupos:** Validar `inscripciones_activas < cupos` ANTES de insertar → 409 `cupos_completos` (regla 3)
4. **Baja alumno → inscripciones a `baja`** (regla 4)
5. **Baja curso → inscripciones a `baja` + des-asignar docentes** (regla 5)
6. **Usuario alumno → `alumno_id` obligatorio**; admin/docente → `alumno_id` nulo (regla 6)
7. **`created_by` / `updated_by`** en toda mutation (regla 7)
8. **Soft delete only** — nunca `DELETE FROM` real (regla 8)

---

## 6. Testing

### Estructura
```
tests/
├── conftest.py              # fixtures: db_session, client, auth_headers
├── unit/
│   ├── test_alumno_service.py
│   ├── test_curso_service.py
│   ├── test_auth_service.py
│   └── test_inscripcion_service.py
└── integration/
    ├── test_alumnos_api.py
    ├── test_cursos_api.py
    ├── test_inscripciones_api.py
    └── test_auth_api.py
```

### Fixtures clave (`conftest.py`)
- `db_session` — `AsyncSession` transaccional con rollback al final
- `client` — `AsyncClient` (httpx) contra app FastAPI
- `admin_user`, `docente_user`, `alumno_user` — usuarios creados en BD
- `auth_headers_admin`, `auth_headers_docente`, `auth_headers_alumno` — dict con `Authorization: Bearer <token>`

### Ejecutar
```bash
# Todos
pytest

# Solo unitarios
pytest tests/unit/ -v

# Solo integración
pytest tests/integration/ -v

# Con coverage
pytest --cov=app --cov-report=term-missing
```

### Cobertura mínima
- Services/repositories: **≥ 80%**
- Endpoints críticos (auth, inscripciones, cupos): **100% de paths**

---

## 7. Base de Datos y Migraciones

### Alembic (async)
```bash
# Nueva migración (después de cambiar modelos)
alembic revision --autogenerate -m "descripcion_corta"

# Aplicar
alembic upgrade head

# Rollback 1 paso
alembic downgrade -1

# Ver historial
alembic history
```

### Convenciones migración
- Nombre: verbo + sujeto + detalle (`add_cupos_to_cursos`, `fix_inscripcion_unique_idx`)
- Una migración = un cambio lógico
- Revisar SQL generado antes de `upgrade`
- `downgrade()` debe ser funcional (no `pass`)

### Docker Postgres
```bash
docker compose up -d          # levanta
docker compose down           # baja (mantiene volúmenes)
docker compose down -v        # baja Y borra datos (reset completo)
docker compose logs -f postgres
```

---

## 8. Autenticación y Roles

### JWT
- Algoritmo: **HS256**
- Expiración: **60 minutos**
- Secret: `SECRET_KEY` en `.env` (generar: `openssl rand -hex 32`)

### Roles y Permisos
| Endpoint | Roles permitidos |
|----------|------------------|
| `/alumnos*` (CRUD) | `admin` |
| `/cursos*` (CRUD) | `admin` |
| `/materias*` | `admin` |
| `/inscripciones*` (POST/DELETE) | `admin` |
| `/inscripciones` GET | `admin`, `docente` (del curso) |
| `/docentes*` (asignación) | `admin` |
| `/docente/me/cursos` | `docente` |
| `/alumno/me/cursos` | `alumno` |
| `/auth/me` | cualquiera autenticado |

### Dependency `require_role(*roles)`
```python
# En router
from app.api.deps import require_role

@router.get("/docente/me/cursos", dependencies=[Depends(require_role("docente"))])
async def mis_cursos(...):
    ...
```

---

## 9. Comandos de Referencia Rápida

| Acción | Comando |
|--------|---------|
| Activar env | `conda activate py3.12` |
| Levantar API dev | `uvicorn app.main:app --reload` |
| Tests | `pytest` |
| Lint + format | `ruff check . && ruff format .` |
| Type check | `mypy --strict app/` |
| Migración nueva | `alembic revision --autogenerate -m "msg"` |
| Aplicar migraciones | `alembic upgrade head` |
| Levantar DB | `docker compose up -d` |
| Ver logs DB | `docker compose logs -f postgres` |
| Generar SECRET_KEY | `openssl rand -hex 32` |

---

## 10. Qué NO Hacer

- ❌ Poner lógica de negocio en routers
- ❌ Usar `Session` sync en código async (usar `AsyncSession`)
- ❌ Hardcodear `DATABASE_URL` o `SECRET_KEY` en código
- ❌ Hacer `DELETE FROM` real (solo `activo=False`)
- ❌ Crear endpoints fuera de `/api/v1/`
- ❌ Commitear `.env` con credenciales reales
- ❌ Ignorar errores de `mypy` o `ruff` sin justificar
- ❌ Testear solo "happy path" — probar 400, 401, 403, 404, 409
- ❌ Mezclar schemas de request y response en una sola clase

---

## 11. Checklist Pre-Commit (mental)

- [ ] `conda activate py3.12` ejecutado
- [ ] Tests pasan (`pytest -x`)
- [ ] `ruff check .` limpio
- [ ] `ruff format --check .` limpio
- [ ] `mypy --strict app/` limpio
- [ ] Si tocó modelos: migración generada y `alembic upgrade head` ok
- [ ] Error codes consistentes (`snake_case`, en `app/core/exceptions.py`)
- [ ] `created_by`/`updated_by` seteados en mutations nuevas
- [ ] Soft delete respeta reglas de propagación (PRD §7 reglas 4-5)
- [ ] Docstrings en services/repositories públicos

---

## 12. Escalamiento

Si una tarea requiere decisión de arquitectura no cubierta en PRD/PLAN:
1. **Detener** la implementación
2. Documentar la duda en un comentario o issue
3. Esperar validación humana antes de continuar

**No inventar** reglas de negocio, endpoints, o esquemas de BD que no estén en PRD.md.

---

> **Recordatorio:** Este archivo es la "constitución" del proyecto para agentes. Si algo choca con PRD.md o PLAN.md, **gana PRD.md**. Actualizar este archivo cuando cambien convenciones.