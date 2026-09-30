# Sistema de Administración de Alumnos - Bunker4

Sistema de gestión de alumnos y cursos para la jornada formativa de Bunker4.

## Stack

- Python 3.12 (managed via conda)
- FastAPI (API REST async)
- SQLAlchemy 2.x (ORM, estilo tipado)
- PostgreSQL 16

## Estado Actual

**MVP implementado y funcional** — El código completo está en el repositorio:
- ✅ Core (config, DB, security, exceptions, logging)
- ✅ Modelos SQLAlchemy + 2 migraciones Alembic
- ✅ Repositorios, Servicios, Routers API v1
- ✅ 182 tests pasando (unit + integración)
- ✅ Templates HTML/Jinja2 (para futuro frontend)
- ✅ Script de bootstrap `create_admin`

Para el detalle de producto leer [PRD.md](./PRD.md).
Para el plan de implementación leer [PLAN.md](./PLAN.md).
Para reglas de trabajo de agentes leer [AGENTS.md](./AGENTS.md).

## Arquitectura de Base de Datos

El proyecto soporta **dos ambientes de base de datos**:

| Entorno | Descripción | Conexión |
|---------|-------------|----------|
| **Local (Docker)** | PostgreSQL 16 via Docker Compose | `postgresql+psycopg://...@localhost:5432/...` |
| **Remoto (Proxmox)** | PostgreSQL 16 en servidor Proxmox (prod/staging) | SSH tunnel / VPN + `DATABASE_URL` en `.env` |

Ambos ambientes usan la misma cadena de migraciones (Alembic). La variable `DATABASE_URL` en `.env` determina el target.

## Prerrequisitos

1. **Conda** instalado (Miniconda o Anaconda).
2. **Docker** + **Docker Compose** (para PostgreSQL local).
3. **Git**.
4. **Acceso al servidor Proxmox** (SSH/VPN) para ambiente remoto — solo necesario para deploy a staging/producción.

## Deploy / Setup local

### 1. Clonar el repositorio

```bash
git clone <repo-url> proyecto_padawans
cd proyecto_padawans
```

### 2. Crear y activar el virtual environment (una sola vez)

Se usa conda para tener un intérprete Python 3.12 aislado. La creación se hace una única vez por máquina.

```bash
conda create -n py3.12 python=3.12
conda activate py3.12
```

### 3. Levantar PostgreSQL Local con Docker Compose

El entorno local usa PostgreSQL 16 via Docker Compose. Se provee `docker-compose.yml` que levanta:

- `postgres:16` en el puerto `5432`
- (opcional) adminer en `8080`

Desde la raíz del proyecto:

```bash
docker compose up -d
```

Para el **entorno remoto (Proxmox)**, no se usa Docker Compose. La conexión se hace via SSH tunnel o VPN apuntando al servidor PostgreSQL 16 en Proxmox, y la `DATABASE_URL` en `.env` apunta a esa conexión.

### 4. Instalar dependencias del proyecto

Una vez dentro del environment `py3.12`:

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copiar `.env.example` a `.env`:

```bash
cp .env.example .env
```

**Importante:** El `.env.example` usa `localhost` para desarrollo local. Si usás Docker Compose, la base está en `localhost:5432`. El `.env` del repo usa `postgres` (nombre del servicio Docker) para que funcione dentro del contenedor de la app. Para desarrollo local **fuera de Docker**, usá `localhost` en tu `.env` personal.

Valores típicos por entorno:

**Local (fuera de Docker, PostgreSQL en Docker Compose):**
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos
SECRET_KEY=<generar-con-openssl-rand-hex-32>
```

**Local (dentro de contenedor app via docker-compose.prod.yml):**
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/bunker4_alumnos
SECRET_KEY=<generar-con-openssl-rand-hex-32>
```

**Remoto (Proxmox via SSH tunnel):**
```
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/bunker4_alumnos
SECRET_KEY=<generar-con-openssl-rand-hex-32>
```

### 6. Aplicar migraciones

```bash
alembic upgrade head
```

### 7. Crear el administrador inicial

```bash
# Opción A: interactivo (recomendado, contraseña oculta)
python -m scripts.create_admin --database-url postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos

# Opción B: con argumentos (para automatización)
python -m scripts.create_admin --database-url postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos --username admin --email admin@bunker4.com --password 'secreto123'
```

> **Nota:** El flag `--database-url` es necesario cuando corrés el script desde el host (fuera de Docker) porque el `.env` del repo apunta al servicio `postgres` de Docker. Si ya estás dentro del contenedor de la app, no hace falta.

El comando crea el primer usuario con rol `admin`, sin `alumno_id`, y registra su propio ID en `created_by` y `updated_by`. Si ese mismo administrador ya existe, termina sin duplicarlo ni cambiar su contraseña.

### 8. Levantar el servidor de desarrollo

```bash
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` y la documentación OpenAPI en `http://localhost:8000/docs`.

### 9. Preparar la base exclusiva de tests

Pytest resetea el esquema al inicio de la sesión, por lo que requiere una base PostgreSQL dedicada. Créela una vez dentro del contenedor PostgreSQL administrado por Compose (este comando no toca la base de desarrollo):

```bash
docker compose up -d postgres
docker compose exec postgres createdb -U postgres bunker4_alumnos_test
```

Antes de ejecutar pytest, exporte explícitamente ambas variables:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos_test'
export ALLOW_TEST_DATABASE_RESET=true
pytest
```

La regla es estricta: el nombre de la base debe terminar exactamente en `_test`, el target normalizado `host + puerto + nombre de base` debe ser distinto del de `DATABASE_URL`, el dialecto debe ser PostgreSQL y la autorización debe ser el valor minúscula exacta `true`. No se admite pytest-xdist porque todos los workers compartirían el mismo esquema.

> **ADVERTENCIA:** pytest aborta antes de construir el engine destructivo si falta alguna variable, si la configuración es ambigua o si `TEST_DATABASE_URL` apunta a desarrollo. Nunca use `bunker4_alumnos` como base de tests.

## Activación del environment en cada arranque (IMPORTANTE)

Cada vez que abras una terminal nueva para trabajar en el proyecto:

```bash
conda activate py3.12
```

Esto es **obligatorio** antes de ejecutar cualquier comando (`uvicorn`, `alembic`, `pytest`, etc.).

### Opcional: activación automática

Si querés que el environment se active solo al entrar al directorio, podés usar [`direnv`](https://direnv.net/) con un `.envrc`:

```bash
# .envrc (no commitear credenciales acá)
conda activate py3.12
```

Y autorizar:

```bash
direnv allow
```

> No se incluye por defecto: si una shell queda con el env activo y se ejecutan tareas ajenas, podrían pisar dependencias. Por eso por defecto el activation es explícito.

## Orden recomendado para arrancar el proyecto

1. `git clone` + `cd`
2. `conda create -n py3.12 python=3.12` (una vez)
3. `conda activate py3.12` (cada arranque)
4. `docker compose up -d` (Postgres)
5. `pip install -r requirements.txt`
6. `cp .env.example .env` y editar (usar `localhost` si corrés fuera de Docker)
7. `alembic upgrade head`
8. `python -m scripts.create_admin --database-url postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos`
9. `uvicorn app.main:app --reload`

## Comandos útiles

| Acción | Comando |
|--------|---------|
| Activar env | `conda activate py3.12` |
| Salir del env | `conda deactivate` |
| Levantar DB (local) | `docker compose up -d` |
| Bajar DB (local) | `docker compose down` |
| Resetear DB local (borra datos) | `docker compose down -v` |
| Logs DB local | `docker compose logs -f postgres` |
| Migraciones (ambos) | `alembic upgrade head` |
| Tests | `TEST_DATABASE_URL=... ALLOW_TEST_DATABASE_RESET=true pytest` |
| Lint | `ruff check .` |
| Formato | `ruff format .` |
| Type check | `mypy --strict app/` |
| Crear admin | `python -m scripts.create_admin --database-url ...` |

## Nota sobre ambientes de Base de Datos

El proyecto está diseñado para **dos ambientes**:
- **Local**: PostgreSQL via Docker Compose (recomendado para desarrollo)
- **Remoto**: PostgreSQL 16 en Proxmox (staging/producción), acceso via SSH tunnel o VPN

Ambos usan la misma cadena de migraciones Alembic. Cambiar de entorno es solo cuestión de actualizar `DATABASE_URL` en `.env` (y tener conectividad al remoto). Docker local es el camino recomendado para desarrollo por consistencia.

## Licencia

Ver [LICENSE](./LICENSE).