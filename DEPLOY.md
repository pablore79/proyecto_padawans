# Guía de despliegue

El despliegue del monorepo usa un único archivo raíz, `docker-compose.yml`.
Este archivo construye el backend desde `backend/Dockerfile`, el frontend desde
`frontend/Dockerfile` y administra los servicios auxiliares necesarios.

## Ruta rápida

1. Cree el archivo `.env` en la raíz del repositorio.
2. Ejecute `./deploy.sh` desde la raíz, o invoque el script mediante su ruta
   absoluta desde otro directorio.
3. Compruebe el estado de los servicios y sus endpoints de salud.

## Requisitos

- Docker Engine con el complemento Docker Compose v2.
- Acceso de escritura al directorio del repositorio para crear y leer `.env`.
- Puertos locales disponibles: `5432`, `8000`, `8080` y `8081`.

## Configuración de entorno

Cree `.env` en la raíz del repositorio. El archivo no debe versionarse ni
contener credenciales reutilizadas.

```bash
# Auth
# Generar con: openssl rand -hex 32
SECRET_KEY=replace_with_a_unique_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Aplicación
APP_NAME="Bunker4 Alumnos"
DEBUG=false
LOG_LEVEL=INFO
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

El servicio `backend` recibe su conexión a PostgreSQL desde
`docker-compose.yml`. El servicio `postgres` conserva sus datos en el volumen
nombrado `postgres_data`; las operaciones habituales de despliegue no eliminan
ese volumen.

## Servicios del monorepo

| Servicio | Definición | Puerto local | Dependencia |
|----------|------------|--------------|-------------|
| `postgres` | Imagen PostgreSQL 16 | `5432` | Volumen `postgres_data` |
| `backend` | `backend/Dockerfile` | `8000` | `postgres` saludable |
| `frontend` | `frontend/Dockerfile` | `8080` | `backend` saludable |
| `adminer` | Imagen Adminer | `8081` | `postgres` saludable |

## Despliegue

Desde la raíz del repositorio, ejecute:

```bash
./deploy.sh
```

El script resuelve la ruta del repositorio y ejecuta el equivalente a:

```bash
docker compose --project-directory . -f docker-compose.yml up -d --build
```

También puede ejecutar el comando anterior directamente desde la raíz. No use
archivos Compose alternativos ni un Dockerfile en la raíz: los Dockerfiles de
cada servicio son `backend/Dockerfile` y `frontend/Dockerfile`.

## Construcción de imágenes

Use `build.sh` para construir las imágenes definidas por el archivo Compose
canónico. El script resuelve la raíz del repositorio, por lo que también puede
invocarse mediante una ruta absoluta desde otro directorio.

```bash
# Construir todas las imágenes
./build.sh

# Construir solo la imagen del backend
./build.sh backend
```

## Recrear el backend y crear el primer administrador

Después de una modificación que afecte la imagen del backend, primero
reconstruya la imagen y recree el servicio. Esto garantiza que el contenedor
incluya los archivos actualizados antes de ejecutar el módulo de inicialización.
Ejecute los siguientes comandos desde la raíz del repositorio.

```bash
./build.sh backend
docker compose -f docker-compose.yml up -d --force-recreate backend
docker compose -f docker-compose.yml exec backend python -m scripts.create_admin
```

El último comando solicita de forma interactiva el nombre de usuario, el correo
electrónico y la contraseña. No incluya credenciales ni contraseñas en comandos,
archivos versionados o historial de terminal.

## Verificación posterior al despliegue

```bash
# Estado de los servicios
docker compose -f docker-compose.yml ps

# Registros de un servicio
docker compose -f docker-compose.yml logs -f backend
docker compose -f docker-compose.yml logs -f frontend

# Endpoints de salud
curl http://localhost:8000/health
curl http://localhost:8080/health
```

## Operación segura

Para detener los servicios sin eliminar los datos de PostgreSQL:

```bash
./down.sh
```

`down.sh` ejecuta `docker compose down` sin aceptar argumentos, por lo que no
puede propagar `-v` ni otras opciones que eliminen volúmenes nombrados. El
volumen `postgres_data` se conserva.

No ejecute comandos que eliminen volúmenes a menos que exista una copia de
seguridad verificada y una autorización explícita para borrar los datos.

## Lista previa al despliegue

- [ ] `SECRET_KEY` fue generado específicamente para el entorno.
- [ ] `DEBUG=false` en entornos no locales.
- [ ] Se revisaron las variables de `.env` sin compartir ni versionar secretos.
- [ ] El archivo canónico `docker-compose.yml` valida con Docker Compose.
- [ ] Se dispone de una copia de seguridad de la base de datos antes de cambios
      operativos relevantes.
