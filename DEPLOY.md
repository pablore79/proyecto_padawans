# DEPLOY.md — Guía de Despliegue

Este documento cubre el despliegue del sistema **Bunker4 Alumnos** en diferentes entornos.

---

## 1. Variables de Entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# App
APP_NAME="Bunker4 Alumnos"
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database (PostgreSQL 16)
# Local Docker:
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos
# Remoto (Proxmox, Cloud SQL, RDS, etc.):
# DATABASE_URL=postgresql+psycopg://user:pass@host:5432/bunker4_alumnos

# Auth (JWT HS256)
# GENERAR CON: openssl rand -hex 32
SECRET_KEY=tu_clave_secreta_de_32_bytes_minimo
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS (orígenes permitidos para frontend)
CORS_ORIGINS=["https://tudominio.com","https://admin.tudominio.com"]

# Paginación
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100

# Postgres (para docker-compose.prod.yml)
POSTGRES_DB=bunker4_alumnos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password_seguro_aqui
```

> **Importante:** Nunca commitees `.env` con credenciales reales. Usa `.env.example` como plantilla.

---

## 2. Despliegue Local con Docker Compose (Desarrollo / Staging)

```bash
# Levantar servicios
docker compose -f docker-compose.yml up -d

# Ver logs
docker compose -f docker-compose.yml logs -f

# Bajar servicios (mantiene volúmenes)
docker compose -f docker-compose.yml down

# Reset completo (borra datos)
docker compose -f docker-compose.yml down -v
```

---

## 3. Despliegue en Producción (VPS / VM)

### Requisitos
- Docker Engine ≥ 24.x
- Docker Compose ≥ 2.x (plugin)
- PostgreSQL 16 (local o remoto)

### Pasos

```bash
# 1. Clonar repo
git clone <repo-url>
cd proyecto_padawans

# 2. Crear .env con variables de producción
cp .env.example .env
# Editar .env con valores reales

# 3. Levantar con compose de producción
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verificar salud
curl http://localhost:8000/docs
curl http://localhost:8000/api/v1/auth/me  # (requiere token)

# 5. Ver logs
docker compose -f docker-compose.prod.yml logs -f app
```

### Variables críticas para producción
| Variable | Acción |
|----------|--------|
| `SECRET_KEY` | **Generar nuevo:** `openssl rand -hex 32` |
| `DEBUG` | `false` |
| `CORS_ORIGINS` | Dominios reales del frontend |
| `DATABASE_URL` | Apuntar a DB remota o local con password seguro |
| `POSTGRES_PASSWORD` | Password fuerte, distinto al de desarrollo |

---

## 4. Despliegue en Cloud Run (GCP)

```bash
# 1. Build y push a Artifact Registry
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT_ID/REPO/bunker4-alumnos

# 2. Desplegar
gcloud run deploy bunker4-alumnos \
  --image REGION-docker.pkg.dev/PROJECT_ID/REPO/bunker4-alumnos \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars="APP_ENV=production,DEBUG=false,LOG_LEVEL=INFO" \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest" \
  --cpu 1 --memory 512Mi --min-instances 0 --max-instances 10
```

> Cloud Run requiere que el puerto sea 8000 (configurado en Dockerfile) y que la app escuche en `0.0.0.0`.

---

## 5. Despliegue en Railway

1. Conectar repo en Railway
2. Agregar servicio PostgreSQL (Railway lo provee)
3. Configurar variables de entorno en el dashboard:
   - `DATABASE_URL` → usar la variable interna de Railway (`${{Postgres.DATABASE_URL}}`)
   - `SECRET_KEY` → generar nuevo
   - `DEBUG=false`
   - `CORS_ORIGINS` → tu dominio
4. Railway detecta `Dockerfile` y despliega automáticamente

---

## 6. Despliegue en Render / Fly.io / Similares

### Render
- **Build Command:** `docker build -t bunker4-alumnos .`
- **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
- Agregar PostgreSQL managed service
- Configurar env vars igual que producción

### Fly.io
```bash
fly launch --dockerfile Dockerfile
fly secrets set DATABASE_URL=... SECRET_KEY=... DEBUG=false
fly deploy
```

---

## 7. Migraciones en Producción

```bash
# Opción A: Via docker compose (recomendado)
docker compose -f docker-compose.prod.yml exec app alembic upgrade head

# Opción B: Directo en contenedor
docker exec bunker4_app alembic upgrade head

# Ver historial
docker compose -f docker-compose.prod.yml exec app alembic history

# Rollback 1 paso (solo si es seguro)
docker compose -f docker-compose.prod.yml exec app alembic downgrade -1
```

> **Regla:** Siempre revisa el SQL generado con `alembic upgrade head --sql` antes de aplicar en producción.

---

## 8. Backup y Restore de Base de Datos

### Backup
```bash
# Local
docker exec bunker4_postgres pg_dump -U postgres bunker4_alumnos > backup_$(date +%F).sql

# Remoto (Proxmox, Cloud SQL, RDS)
pg_dump -h HOST -U USER -d bunker4_alumnos > backup_$(date +%F).sql
```

### Restore
```bash
# Detener app para evitar conexiones
docker compose -f docker-compose.prod.yml stop app

# Restaurar
docker exec -i bunker4_postgres psql -U postgres bunker4_alumnos < backup_2026-01-15.sql

# Levantar app
docker compose -f docker-compose.prod.yml start app
```

---

## 9. Checklist Pre-Deploy

- [ ] `SECRET_KEY` generado con `openssl rand -hex 32`
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS` solo dominios de producción
- [ ] `DATABASE_URL` apunta a DB correcta (remota o local con password seguro)
- [ ] `POSTGRES_PASSWORD` fuerte y único
- [ ] Tests pasan localmente (`pytest -q`)
- [ ] Lint y type-check pasan (`ruff check . && mypy --strict app/`)
- [ ] Migraciones revisadas (`alembic upgrade head --sql`)
- [ ] Healthcheck `/docs` responde 200
- [ ] Backup de DB programado (cron, Cloud Scheduler, etc.)

---

## 10. Rollback Rápido

```bash
# Si el deploy falla y necesitas volver a la versión anterior
docker compose -f docker-compose.prod.yml pull  # si usas registry
docker compose -f docker-compose.prod.yml up -d --force-recreate

# O volver al commit anterior y redeploy
git revert HEAD~1
git push
# CI/CD redeploya automáticamente
```

---

## 11. Monitoreo Básico

- **Health endpoint:** `GET /docs` (200 = OK)
- **Métricas:** Logs estructurados JSON en stdout (ver `app/core/logging.py`)
- **Logs:** `docker compose logs -f app` o sistema de logs del proveedor (Cloud Logging, Datadog, etc.)

---

## 12. Escalado Horizontal (Opcional)

Para múltiples instancias detrás de load balancer:

1. Usar **Redis** para rate limiting / cache (no implementado aún)
2. DB connection pooling: `psycopg[pool]` ya está en requirements
3. Workers: `--workers 4` en uvicorn (ajustar según CPU)
4. Session affinity **no** requerida (JWT stateless)

---

> **Nota:** Esta guía asume PostgreSQL 16. Para otros proveedores managed (Cloud SQL, RDS, Neon, Supabase), solo cambia `DATABASE_URL` y asegura conectividad de red (VPC, SSL, IPs permitidas).