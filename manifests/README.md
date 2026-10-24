# Manifiestos Kubernetes (microk8s)

Port de `docker-compose.yml` para microk8s. El servicio `postgres` **no** se porta: la base corre en `10.10.153.13:5432`.

## Contenido

| Archivo | Recursos |
|---------|----------|
| `namespace.yaml` | Namespace `bunker4` |
| `secret.yaml` | Secret `bunker4-env` con las variables de `.env` (valores a completar) |
| `backend.yaml` | Deployment + Service `backend` (8000, ClusterIP) |
| `frontend.yaml` | Deployment + Service `frontend` (8080, NodePort 30080) |
| `adminer.yaml` | Deployment + Service `adminer` (8080, NodePort 30081) |

## Pasos

1. Habilitar el registry local de microk8s (una vez):
   ```bash
   microk8s enable registry
   ```
2. Construir y subir las imágenes:
   ```bash
   docker build -t localhost:32000/bunker4-backend:latest backend
   docker build -t localhost:32000/bunker4-frontend:latest frontend
   docker push localhost:32000/bunker4-backend:latest
   docker push localhost:32000/bunker4-frontend:latest
   ```
   Si el registry no es accesible por `localhost:32000` desde Docker, configurá `insecure-registries` según la doc de microk8s.
3. Completar los `<COMPLETAR>` de `secret.yaml` con los valores de `.env`, o crear el Secret directamente desde el archivo sin guardar credenciales en el repo:
   ```bash
   microk8s kubectl create namespace bunker4 --dry-run=client -o yaml | microk8s kubectl apply -f -
   microk8s kubectl -n bunker4 create secret generic bunker4-env --from-env-file=.env \
     --dry-run=client -o yaml | microk8s kubectl apply -f -
   ```
   Si usás la segunda vía, no apliques `secret.yaml`.
4. Aplicar el resto:
   ```bash
   microk8s kubectl apply -f manifests/namespace.yaml
   microk8s kubectl apply -f manifests/backend.yaml -f manifests/frontend.yaml -f manifests/adminer.yaml
   ```
5. Verificar:
   ```bash
   microk8s kubectl -n bunker4 get pods,svc
   microk8s kubectl -n bunker4 logs deploy/backend
   ```

## Notas

- El backend ejecuta `alembic upgrade head` al arrancar (ver `backend/Dockerfile`). La base remota debe ser accesible desde el nodo.
- `CORS_ORIGINS` en `secret.yaml` tiene que apuntar a la URL real del frontend (`http://<IP_NODO>:30080`).
- `secret.yaml` contiene placeholders. No commitear con valores reales.
