# Propuesta de Frontend — Bunker4 Alumnos

## Contexto
Backend: **FastAPI** (API REST + OpenAPI en `/docs`), Python 3.12, SQLAlchemy 2.x async, PostgreSQL 16.
Arquitectura: Clean/Hexagonal simplificada.

## Requisitos del equipo
- **Evitar**: Next.js, React, Vue, TypeScript, transpilación, build steps.
- **Preferir**: JavaScript vainilla (vanilla) lo más nativo posible.
- **Cero dependencias** o dependencias mínimas solo CDN.

---

## Opciones evaluadas

| Opción | Build step | Tamaño | Curva | Reactividad | Ideal para |
|--------|------------|--------|-------|-------------|------------|
| **HTMX + Jinja2** | ❌ | ~14 KB | Baja | Server-side | CRUD, tablas, formularios, validaciones server-side |
| **HTMX + Alpine.js** | ❌ | ~30 KB | Media | Híbrida (cliente + server) | UI reactiva local + llamadas server |
| **Vanilla ES Modules** | ❌ | 0 KB | Alta | Manual (custom) | Control total, equipo experto en JS |

---

## Recomendación: **HTMX + Jinja2** (con Alpine.js opcional)

### Por qué
1. **FastAPI ya trae `Jinja2Templates`** — renderizado server-side nativo.
2. **HTMX** pone AJAX, WebSockets, SSE, history, boost en **atributos HTML** (`hx-get`, `hx-post`, `hx-target`, `hx-swap`).
3. **Zero build**, **zero transpilation**, se carga con `<script src="https://unpkg.com/htmx.org@1.9.12">`.
4. Lógica de UI y validaciones viven en el **backend** (coherente con Clean Architecture).
5. Alpine.js se añade solo si hace falta reactividad local (modales, tabs, filtros instantáneos) — **30 KB totales**.

### Ejemplo de integración

**Backend (FastAPI + Jinja2)**
```python
# main.py
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@router.get("/alumnos", response_class=HTMLResponse)
async def listar_alumnos(request: Request, db: AsyncSession = Depends(get_db)):
    alumnos = await alumno_repo.list(db)
    return templates.TemplateResponse("alumnos/list.html", {"request": request, "alumnos": alumnos})
```

**Template base (`templates/base.html`)**
```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}Bunker4 Alumnos{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@1.9.12" defer></script>
  <!-- Alpine.js opcional: <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js" defer></script> -->
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  {% block content %}{% endblock %}
</body>
</html>
```

**Listado con HTMX (`templates/alumnos/list.html`)**
```html
{% extends "base.html" %}
{% block content %}
<table>
  <thead><tr><th>Nombre</th><th>DNI</th><th>Acciones</th></tr></thead>
  <tbody hx-get="/api/v1/alumnos/partial" hx-trigger="load, alumnoChanged from:body">
    {% for a in alumnos %}{% include "alumnos/row.html" %}{% endfor %}
  </tbody>
</table>
<button hx-post "/api/v1/alumnos" hx-target="tbody" hx-swap="beforeend">
  Agregar alumno
</button>
{% endblock %}
```

**Fila parcial (`templates/alumnos/row.html`)**
```html
<tr>
  <td>{{ a.nombre }}</td>
  <td>{{ a.dni }}</td>
  <td>
    <button hx-delete="/api/v1/alumnos/{{ a.id }}" hx-swap="outerHTML" hx-confirm="¿Dar de baja?">
      Baja
    </button>
  </td>
</tr>
```

---

## Tradeoffs a considerar

| Ventaja | Desventaja |
|---------|------------|
| Entrega rápida, menos JS que mantener | Lógica de presentación en servidor |
| SEO natural, accesibilidad nativa | Menos "app-like" (transiciones, offline) |
| Coherente con backend Python | Requiere endpoints que devuelvan HTML parcial |
| Equipo fullstack trabaja en un lenguaje | No es SPA pura |

---

## Próximos pasos si se aprueba
1. Añadir `jinja2` a `requirements.txt` (ya incluido).
2. Crear estructura `templates/` y `static/`.
3. Implementar endpoints que devuelvan `HTMLResponse` + parciales.
4. (Opcional) Añadir Alpine.js solo donde haga falta reactividad local.

---

## Decisión
- [ ] Aprobar HTMX + Jinja2
- [ ] Aprobar HTMX + Alpine.js (reactividad local)
- [ ] Evaluar Vanilla ES Modules (control total)
- [ ] Otra: _______________