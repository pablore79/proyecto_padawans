from pathlib import Path

TEMPLATE_PATH = Path(__file__).parents[2] / "templates" / "alumnos" / "_form.html"


def test_alumno_form_preserves_json_api_contract() -> None:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "hx-post=" not in template
    assert 'name="_method"' not in template
    assert "htmx:afterRequest" not in template
    assert "</form    </div>" not in template
    assert "</form>" in template
    assert "fetch(endpoint" in template
    assert "/api/v1/alumnos/{{ alumno.id }}" in template
    assert "{% else %}/api/v1/alumnos{% endif %}" in template
    assert "{% if alumno %}PATCH{% else %}POST{% endif %}" in template
    assert "'Content-Type': 'application/json'" in template
    assert "'Authorization': `Bearer ${token}`" in template
    assert "localStorage.getItem('auth_token')" in template
    assert "body: JSON.stringify(payload)" in template

    for field in ("dni", "nombre", "apellido", "email"):
        assert f"{field}: form.elements.{field}.value.trim()" in template

    for field in (
        "telefono",
        "fecha_nacimiento",
        "usuario_github",
        "usuario_gitlab",
        "perfil_linkedin",
    ):
        assert f"{field}: optionalValue('{field}')" in template

    assert "return value === '' ? null : value" in template
    assert "payload.activo = form.elements.activo.checked" in template
    assert "if (submitButton.disabled) return" in template
    assert "response.status === 200 || response.status === 201" in template
    assert "response.status === 401 || response.status === 403" in template
    assert "response.status === 409" in template
    assert "response.status === 422" in template
    assert "htmx.trigger(tableBody, 'load')" in template
    assert "form.closest('.modal-overlay')?.remove()" in template
    assert "submitButton.disabled = false" in template
