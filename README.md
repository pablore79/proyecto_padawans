# Sistema de Administración de Alumnos - Bunker4 (Monorepo)

Sistema de gestión de alumnos y cursos para la jornada formativa de Bunker4, preparado para arquitectura de microservicios.

## Estructura del Monorepo

```
proyecto_padawans/
├── backend/              # FastAPI REST API (microservicio backend)
│   ├── app/              # Código de la aplicación
│   │   ├── api/          # Routers API v1
│   │   ├── core/         # Config, DB, Security, Exceptions, Logging
│   │   ├── models/       # Modelos SQLAlchemy
│   │   ├── repositories/ # Capa de acceso a datos
│   │   ├── schemas/      # DTOs Pydantic
│   │   ├── services/     # Lógica de negocio
│   │   └── main.py       # Entry point
│   ├── alembic/          # Migraciones de BD
│   ├── tests/            # Tests unitarios e integración
│   ├── safety_tests/     # Guards de seguridad para tests
│   ├── scripts/          # Scripts de utilidad (create_admin)
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/             # FastAPI BFF (Backend for Frontend)
│   ├── app/              # Código de la aplicación
│   │   ├── api/          # Rutas HTML + Proxy a backend
│   │   ├── core/         # Config, Logging, Exceptions
│   │   └── main.py       # Entry point
│   ├── templates/        # Templates Jinja2
│   ├── static/           # Archivos estáticos (CSS, JS)
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docker-compose.yml    # Orquesta backend + frontend + postgres
├── build.sh              # Detiene el proyecto y construye imágenes Compose
├── deploy.sh             # Construye y recrea los servicios Compose
├── down.sh               # Detiene servicios sin borrar volúmenes
├── .env.example          # Variables de entorno ejemplo
├── PRD.md                # Requisitos del producto
├── PLAN.md               # Plan de implementación
├── AGENTS.md             # Instrucciones para agentes IA
└── README.md             # Este archivo
```

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x async, PostgreSQL 16
- **Frontend**: Python 3.12, FastAPI, Jinja2, HTMX
- **Infra**: Docker Compose, PostgreSQL 16

## Estado Actual

**MVP implementado y funcional** — Monorepo con arquitectura preparada para microservicios:

- ✅ Backend API REST completa (alumnos, cursos, materias, inscripciones, docentes, auth)
- ✅ Frontend BFF con templates Jinja2 + HTMX (proxy transparente a backend API)
- ✅ 182 tests pasando (unit + integración) en backend
- ✅ Migraciones Alembic
- ✅ Script de bootstrap `create_admin`
- ✅ Docker Compose para desarrollo local

Para el detalle de producto leer [PRD.md](./PRD.md).
Para el plan de implementación leer [PLAN.md](./PLAN.md).
Para reglas de trabajo de agentes leer [AGENTS.md](./AGENTS.md).

## Prerrequisitos

1. **Conda** instalado (Miniconda o Anaconda).
2. **Docker** + **Docker Compose** (para PostgreSQL local).
3. **Git**.
4. **Acceso al servidor Proxmox** (SSH/VPN) para ambiente remoto — solo necesario para deploy a staging/producción.

## Deploy / Setup Local con Docker Compose (Recomendado)

### 1. Clonar el repositorio

```bash
git clone <repo-url> proyecto_padawans
cd proyecto_padawans
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores (SECRET_KEY, etc.)
```

### 3. Construir y desplegar toda la stack con Docker Compose

```bash
./deploy.sh
```

El script construye las imágenes y recrea los contenedores para aplicar los
cambios. Puede ejecutarse desde la raíz o mediante una ruta absoluta.

Esto levanta:

- **PostgreSQL** en `localhost:5432`
- **Backend API** en `localhost:8000` (docs en `localhost:8000/docs`)
- **Frontend BFF** en `localhost:8080` (UI en `localhost:8080`)
- **Adminer** en `localhost:8081` (UI para BD)

### 4. Aplicar migraciones y crear admin

```bash
# Ejecutar migraciones en el backend
docker compose exec backend alembic upgrade head

# Crear usuario admin inicial
docker compose exec backend python -m scripts.create_admin
```

### 5. Acceder a la aplicación

- **Frontend (UI)**: <http://localhost:8080>
- **Backend API Docs**: <http://localhost:8000/docs>
- **Adminer**: <http://localhost:8081> (Server: `postgres`, User: `postgres`, Pass: `postgres`, DB: `bunker4_alumnos`)

## Operación y despliegue

## Kubernetes

Los manifiestos de Kubernetes usan el namespace `bunker4`. Antes de aplicar el
backend, creá el Secret `bunker4-env` a partir del archivo `.env` local. De este
modo, las credenciales no quedan escritas en un manifiesto versionado.

Desde la raíz del repositorio:

```bash
kubectl create secret generic bunker4-env \
  --namespace bunker4 \
  --from-env-file=.env

kubectl apply -f manifests/backend.yaml
```

Si el Secret ya existe y necesitás actualizarlo con el contenido actual de
`.env`, generá su definición localmente y aplicala:

```bash
kubectl create secret generic bunker4-env \
  --namespace bunker4 \
  --from-env-file=.env \
  --dry-run=client \
  --output=yaml | kubectl apply -f -
```

Verificá la creación del Secret y el inicio del Pod:

```bash
kubectl get secret bunker4-env -n bunker4
kubectl get pods -n bunker4 -w
```

> No versionar `.env` ni la salida de estos comandos: los valores de un Secret
> codificados en Base64 no están cifrados.

### Requisitos

- Docker Engine con Docker Compose v2.
- Un archivo `.env` en la raíz, creado desde `.env.example`, con un `SECRET_KEY`
  único para el entorno.
- Puertos locales disponibles: `5432`, `8000`, `8080` y `8081`.

### Scripts de la raíz

| Acción                | Comando               | Efecto                                                                     |
| --------------------- | --------------------- | -------------------------------------------------------------------------- |
| Desplegar cambios     | `./deploy.sh`         | Construye y ejecuta `up -d --build --force-recreate`.                      |
| Construir imágenes    | `./build.sh`          | Detiene el proyecto sin borrar volúmenes y construye backend y frontend.   |
| Construir un servicio | `./build.sh frontend` | Detiene el proyecto y construye solo el servicio indicado.                 |
| Detener servicios     | `./down.sh`           | Ejecuta `docker compose down` sin propagar opciones para borrar volúmenes. |

Los datos de PostgreSQL se conservan en el volumen nombrado `postgres_data`.
No uses `docker compose down -v` salvo que exista un respaldo verificado y se
haya autorizado explícitamente el borrado de datos.

### Verificación posterior al despliegue

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8080/health
```

Para reconstruir el backend antes de crear el primer administrador, ejecutá
`./deploy.sh` y luego:

```bash
docker compose exec backend python -m scripts.create_admin
```

## Desarrollo Local (Sin Docker para la App)

Si preferís correr la app fuera de Docker para desarrollo con hot-reload:

### 1. Levantar solo PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Crear y activar environment conda

```bash
conda create -n py3.12 python=3.12  # una sola vez
conda activate py3.12               # cada arranque
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt

# Configurar .env.local con DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos
cp ../.env.example .env
# Editar .env con valores locales

alembic upgrade head
python -m scripts.create_admin
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend (en otra terminal)

```bash
cd frontend
pip install -r requirements.txt

# Configurar .env.local con BACKEND_URL=http://localhost:8000
cp ../.env.example .env
# Editar .env con valores locales

uvicorn app.main:app --reload --port 8080
```

## Variables de Entorno

### Backend (`backend/.env`)

| Variable                      | Descripción                                            | Default                     |
| ----------------------------- | ------------------------------------------------------ | --------------------------- |
| `DATABASE_URL`                | URL de conexión PostgreSQL                             | Requerida                   |
| `SECRET_KEY`                  | Clave secreta JWT (generar con `openssl rand -hex 32`) | Requerida                   |
| `ALGORITHM`                   | Algoritmo JWT                                          | `HS256`                     |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración token                                       | `60`                        |
| `CORS_ORIGINS`                | Orígenes CORS permitidos                               | `["http://localhost:8080"]` |
| `APP_NAME`                    | Nombre de la app                                       | `Bunker4 Alumnos API`       |
| `DEBUG`                       | Modo debug                                             | `false`                     |
| `LOG_LEVEL`                   | Nivel de log                                           | `INFO`                      |

### Frontend (`frontend/.env`)

| Variable                      | Descripción                           | Default                                                          |
| ----------------------------- | ------------------------------------- | ---------------------------------------------------------------- |
| `BACKEND_URL`                 | URL del backend API                   | `http://backend:8000` (Docker) / `http://localhost:8000` (local) |
| `SECRET_KEY`                  | Clave secreta JWT (misma que backend) | Requerida                                                        |
| `ALGORITHM`                   | Algoritmo JWT                         | `HS256`                                                          |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración token                      | `60`                                                             |
| `CORS_ORIGINS`                | Orígenes CORS permitidos              | `["http://localhost:8080"]`                                      |
| `APP_NAME`                    | Nombre de la app                      | `Bunker4 Alumnos Frontend`                                       |
| `DEBUG`                       | Modo debug                            | `false`                                                          |
| `LOG_LEVEL`                   | Nivel de log                          | `INFO`                                                           |

## Testing

Los tests se ejecutan en el **backend**:

```bash
cd backend

# Crear base de tests (una vez)
docker compose up -d postgres
docker compose exec postgres createdb -U postgres bunker4_alumnos_test

# Ejecutar tests
export TEST_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos_test'
export ALLOW_TEST_DATABASE_RESET=true
pytest

# Con coverage
pytest --cov=app --cov-report=term-missing
```

## Comandos Útiles

### Docker Compose

| Acción                    | Comando                             |
| ------------------------- | ----------------------------------- |
| Desplegar todo            | `./deploy.sh`                       |
| Levantar solo DB          | `docker compose up -d postgres`     |
| Bajar todo                | `docker compose down`               |
| Resetear DB (borra datos) | `docker compose down -v`            |
| Logs backend              | `docker compose logs -f backend`    |
| Logs frontend             | `docker compose logs -f frontend`   |
| Logs DB                   | `docker compose logs -f postgres`   |
| Shell en backend          | `docker compose exec backend bash`  |
| Shell en frontend         | `docker compose exec frontend bash` |

### Backend (dentro de `backend/`)

| Acción          | Comando                                                       |
| --------------- | ------------------------------------------------------------- |
| Instalar deps   | `pip install -r requirements.txt`                             |
| Migraciones     | `alembic upgrade head`                                        |
| Nueva migración | `alembic revision --autogenerate -m "descripcion"`            |
| Tests           | `TEST_DATABASE_URL=... ALLOW_TEST_DATABASE_RESET=true pytest` |
| Lint            | `ruff check .`                                                |
| Formato         | `ruff format .`                                               |
| Type check      | `mypy --strict app/`                                          |
| Crear admin     | `python -m scripts.create_admin`                              |
| Servidor dev    | `uvicorn app.main:app --reload`                               |

### Frontend (dentro de `frontend/`)

| Acción        | Comando                           |
| ------------- | --------------------------------- |
| Instalar deps | `pip install -r requirements.txt` |
| Lint          | `ruff check .`                    |
| Formato       | `ruff format .`                   |
| Type check    | `mypy --strict app/`              |
| Servidor dev  | `uvicorn app.main:app --reload`   |

## Ambientes de Base de Datos

El proyecto soporta **dos ambientes**:

| Entorno              | Descripción                                   | Conexión                                                                |
| -------------------- | --------------------------------------------- | ----------------------------------------------------------------------- |
| **Local (Docker)**   | PostgreSQL 16 via Docker Compose              | `postgresql+psycopg://postgres:postgres@postgres:5432/bunker4_alumnos`  |
| **Local (Host)**     | PostgreSQL 16 via Docker Compose, app en host | `postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos` |
| **Remoto (Proxmox)** | PostgreSQL 16 en servidor Proxmox             | SSH tunnel / VPN + `DATABASE_URL` en `.env`                             |

Ambos ambientes usan la misma cadena de migraciones (Alembic). La variable `DATABASE_URL` en `.env` del backend determina el target.

## Arquitectura BFF (Backend for Frontend)

El **frontend** actúa como BFF:

1. Sirve templates HTML (Jinja2) y archivos estáticos
2. Proxy transparente: todas las llamadas `/api/v1/*` se reenvían al **backend**
3. Maneja autenticación: valida tokens con el backend via `/api/v1/auth/me`
4. Inyecta token en requests proxificados al backend

Esto permite:

- Separación clara de responsabilidades
- Backend pura API REST (reutilizable por otros clientes)
- Frontend independiente, escalable por separado
- Migración futura a SPA (React/Vue) sin tocar backend

## Kubernetes secrets

Pasos realizados

```shell
kubectl get secrets -n bunker4
kubectl delete secret bunker4-env -n bunker4
kubectl -n bunker4 create secret generic bunker4-env --from-env-file=.env --dry-run=client -o yaml
kubectl -n bunker4 create secret generic bunker4-env --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -
```

## Licencia

Ver [LICENSE](./LICENSE).
