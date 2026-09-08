# Sistema de Administración de Alumnos - Bunker4

Sistema de gestión de alumnos y cursos para la jornada formativa de Bunker4.

## Stack

- Python 3.12 (managed via conda)
- FastAPI (API REST async)
- SQLAlchemy 2.x (ORM, estilo tipado)
- PostgreSQL 16

## Estado

Este repositorio contiene la documentación inicial (PRD, PLAN, AGENTS, requirements). El esqueleto de código se incorpora en una etapa posterior.

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
- (opcional) adminer o pgadmin en `8080`/`5050`

Desde la raíz del proyecto:

```bash
docker compose up -d
```

Para el **entorno remoto (Proxmox)**, no se usa Docker Compose. La conexión se hace via SSH tunnel o VPN apuntando al servidor PostgreSQL 16 en Proxmox, y la `DATABASE_URL` en `.env` apunta a esa conexión.

### 4. Instalar dependencias del proyecto

Una vez dentro del environment `py3.12`, instalar las dependencias. Eso requiere `requirements.txt` (a incorporar con el esqueleto). Mientras tanto:

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy[asyncio] "psycopg[binary]" pydantic-settings alembic
```

Para versiones fijas, usar el futuro `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copiar `.env.example` a `.env` (ambos archivos se incorporan con el esqueleto):

```bash
cp .env.example .env
```

Valores típicos por entorno:

**Local (Docker):**
```
DATABASE_URL=postgresql+psycopg://bunker4:bunker4@localhost:5432/bunker4
SECRET_KEY=<generar-con-openssl-rand-hex-32>
ENVIRONMENT=local
```

**Remoto (Proxmox via SSH tunnel):**
```
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5433/bunker4
SECRET_KEY=<generar-con-openssl-rand-hex-32>
ENVIRONMENT=staging
```

### 6. Aplicar migraciones (cuando existan)

```bash
alembic upgrade head
```

### 7. Levantar el servidor de desarrollo

```bash
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` y la documentación OpenAPI en `http://localhost:8000/docs`.

## Activación del environment en cada arranque (IMPORTANTE)

Cada vez que abras una terminal nueva para trabajar en el proyecto:

```bash
conda activate py3.12
```

Esto es**obligatorio** antes de ejecutar cualquier comando (`uvicorn`, `alembic`, `pytest`, etc.).

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
5. `pip install -r requirements.txt` (cuando exista)
6. `cp .env.example .env` y editar
7. `alembic upgrade head` (cuando existan migraciones)
8. `uvicorn app.main:app --reload`

## Comandos útiles

| Acción                    | Comando                               |
| ------------------------- | ------------------------------------- |
| Activar env               | `conda activate py3.12`               |
| Salir del env             | `conda deactivate`                    |
| Levantar DB (local)       | `docker compose up -d`                |
| Bajar DB (local)          | `docker compose down`                 |
| Resetear DB local (borra datos) | `docker compose down -v`        |
| Logs DB local             | `docker compose logs -f postgres`     |
| Migraciones (ambos)       | `alembic upgrade head`                |
| Tests                     | `pytest` (cuando existan)             |
| Lint                      | `ruff check .` (cuando exista config) |
| Formato                   | `ruff format .`                       |

## Nota sobre ambientes de Base de Datos

El proyecto está diseñado para **dos ambientes**:
- **Local**: PostgreSQL via Docker Compose (recomendado para desarrollo)
- **Remoto**: PostgreSQL 16 en Proxmox (staging/producción), acceso via SSH tunnel o VPN

Ambos usan la misma cadena de migraciones Alembic. Cambiar de entorno es solo cuestión de actualizar `DATABASE_URL` en `.env` (y tener conectividad al remoto). Docker local es el camino recomendado para desarrollo por consistencia.

## Licencia

Ver [LICENSE](./LICENSE).
