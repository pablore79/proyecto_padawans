# Sistema de Administración de Alumnos - Bunker4

Sistema de gestión de alumnos y cursos para la jornada formativa de Bunker4.

## Stack

- Python 3.12 (managed via conda)
- FastAPI (API REST async)
- SQLAlchemy 2.x (ORM, estilo tipado)
- PostgreSQL 16

## Estado

Este repositorio contiene la documentación inicial (PRD, PLAN, AGENTS, requirements). El archivo "propuesta_frontend.md" es sólo eso, una propuesta. El esqueleto de código se incorpora en una etapa posterior.

Para el detalle de producto leer [PRD.md](./PRD.md).
Para el plan de implementación leer [PLAN.md](./PLAN.md).
Para reglas de trabajo de agentes leer [AGENTS.md](./AGENTS.md).

## Prerrequisitos

1. **Conda** instalado (Miniconda o Anaconda).
2. **Docker** + **Docker Compose** (para PostgreSQL y opcionalmente adminer/pgadmin).
3. **Git**.

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

### 3. Levantar PostgreSQL con Docker Compose

El sistema requiere PostgreSQL 16. Se provee `docker-compose.yml` (a incorporar con el esqueleto) que levanta:

- `postgres:16` en el puerto `5432`
- (opcional) adminer o pgadmin en `8080`/`5050`

Desde la raíz del proyecto:

```bash
docker compose up -d
```

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

Valores típicos:

```
DATABASE_URL=postgresql+psycopg://bunker4:bunker4@localhost:5432/bunker4
SECRET_KEY=<generar-con-openssl-rand-hex-32>
ENVIRONMENT=local
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
| Levantar DB               | `docker compose up -d`                |
| Bajar DB                  | `docker compose down`                 |
| Resetear DB (borra datos) | `docker compose down -v`              |
| Logs de DB                | `docker compose logs -f postgres`     |
| Tests                     | `pytest` (cuando existan)             |
| Lint                      | `ruff check .` (cuando exista config) |
| Formato                   | `ruff format .`                       |

## Nota sobre Postgres embebido vs Docker

Si no querés usar Docker y ya tenés Postgres 16 instalado localmente, podés crear la DB y usuario manualmente y apuntar `DATABASE_URL` a ella. Lo escribo porque complica regularmente a equipos nuevos. Docker es el camino recomendado para consistencia.

## Licencia

Ver [LICENSE](./LICENSE).
