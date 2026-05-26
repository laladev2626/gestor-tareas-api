# Tests para los endpoints de tareas: prioridad en casos de error y casos limite

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app


# Motor en memoria con StaticPool para aislamiento total entre tests
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture()
def client():
    """Crea las tablas antes de cada test y las destruye despues."""
    Base.metadata.create_all(bind=engine_test)

    def _override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _create_task(client, **overrides):
    """Crea una tarea con valores por defecto y devuelve la respuesta JSON."""
    payload = {"title": "Tarea de prueba", **overrides}
    resp = client.post("/tasks/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ===========================================================================
# GET /tasks/ — casos de error y limite
# ===========================================================================
class TestListTasks:
    def test_list_empty(self, client):
        """Lista vacia cuando no hay tareas."""
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_multiple(self, client):
        """Devuelve todas las tareas creadas."""
        _create_task(client, title="A")
        _create_task(client, title="B")
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ===========================================================================
# GET /tasks/{task_id} — casos de error y limite
# ===========================================================================
class TestGetTask:
    def test_not_found(self, client):
        """404 con detail correcto si el id no existe."""
        resp = client.get("/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_not_found_zero_id(self, client):
        """Id 0 no existe; devuelve 404."""
        resp = client.get("/tasks/0")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_not_found_negative_id(self, client):
        """Id negativo no existe; devuelve 404."""
        resp = client.get("/tasks/-1")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_invalid_id_type(self, client):
        """Id no numerico devuelve 422."""
        resp = client.get("/tasks/abc")
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_get_existing(self, client):
        """Recupera una tarea existente con todos sus campos."""
        created = _create_task(client)
        resp = client.get(f"/tasks/{created['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == created["id"]
        assert data["title"] == created["title"]
        assert data["status"] == "pending"
        assert "created_at" in data


# ===========================================================================
# POST /tasks/ — casos de error y limite
# ===========================================================================
class TestCreateTask:
    def test_missing_title(self, client):
        """Falta el campo obligatorio title; devuelve 422."""
        resp = client.post("/tasks/", json={})
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_null_title(self, client):
        """Title explicito como null; devuelve 422."""
        resp = client.post("/tasks/", json={"title": None})
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_invalid_status(self, client):
        """Estado no permitido en el enum; devuelve 422."""
        resp = client.post(
            "/tasks/", json={"title": "X", "status": "invalid"}
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_invalid_body_not_json(self, client):
        """Cuerpo que no es JSON valido; devuelve 422."""
        resp = client.post(
            "/tasks/",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_create_defaults(self, client):
        """Crea tarea solo con titulo; status default pending, description null."""
        data = _create_task(client)
        assert data["status"] == "pending"
        assert data["description"] is None
        assert "id" in data
        assert "created_at" in data

    def test_create_all_fields(self, client):
        """Crea tarea con todos los campos explicitos."""
        data = _create_task(
            client,
            title="Completa",
            description="Desc",
            status="in_progress",
        )
        assert data["title"] == "Completa"
        assert data["description"] == "Desc"
        assert data["status"] == "in_progress"

    def test_create_with_done_status(self, client):
        """Permite crear directamente con status done."""
        data = _create_task(client, status="done")
        assert data["status"] == "done"

    def test_create_empty_description(self, client):
        """Descripcion como cadena vacia se acepta."""
        data = _create_task(client, description="")
        assert data["description"] == ""

    def test_create_long_title(self, client):
        """Titulo con 255 caracteres se acepta."""
        title = "A" * 255
        data = _create_task(client, title=title)
        assert data["title"] == title


# ===========================================================================
# PATCH /tasks/{task_id} — casos de error y limite
# ===========================================================================
class TestUpdateTask:
    def test_not_found(self, client):
        """404 con detail al intentar actualizar tarea inexistente."""
        resp = client.patch("/tasks/999", json={"title": "X"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_invalid_status(self, client):
        """Estado no valido en el enum; devuelve 422."""
        created = _create_task(client)
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "bad"}
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_invalid_id_type(self, client):
        """Id no numerico en PATCH; devuelve 422."""
        resp = client.patch("/tasks/abc", json={"title": "X"})
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_empty_body(self, client):
        """Body vacio no modifica nada; devuelve 200 con datos sin cambios."""
        created = _create_task(client, title="Original")
        resp = client.patch(f"/tasks/{created['id']}", json={})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Original"

    def test_update_title(self, client):
        """Actualiza solo el titulo."""
        created = _create_task(client, title="Viejo")
        resp = client.patch(f"/tasks/{created['id']}", json={"title": "Nuevo"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Nuevo"
        assert resp.json()["description"] == created["description"]

    def test_update_description(self, client):
        """Actualiza solo la descripcion."""
        created = _create_task(client, description="Vieja")
        resp = client.patch(
            f"/tasks/{created['id']}", json={"description": "Nueva"}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Nueva"

    def test_update_status(self, client):
        """Actualiza solo el estado."""
        created = _create_task(client)
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "done"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    def test_update_multiple_fields(self, client):
        """Actualiza titulo y estado a la vez."""
        created = _create_task(client)
        resp = client.patch(
            f"/tasks/{created['id']}",
            json={"title": "Multi", "status": "in_progress"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Multi"
        assert data["status"] == "in_progress"

    def test_set_description_to_null(self, client):
        """Permite establecer description a null explicitamente."""
        created = _create_task(client, description="Algo")
        resp = client.patch(
            f"/tasks/{created['id']}", json={"description": None}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] is None


# ===========================================================================
# DELETE /tasks/{task_id} — casos de error y limite
# ===========================================================================
class TestDeleteTask:
    def test_not_found(self, client):
        """404 con detail al intentar eliminar tarea inexistente."""
        resp = client.delete("/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_invalid_id_type(self, client):
        """Id no numerico en DELETE; devuelve 422."""
        resp = client.delete("/tasks/abc")
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_delete_existing(self, client):
        """Elimina tarea y devuelve 204 sin cuerpo."""
        created = _create_task(client)
        resp = client.delete(f"/tasks/{created['id']}")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_delete_then_get_returns_404(self, client):
        """Tras eliminar, la tarea ya no es accesible."""
        created = _create_task(client)
        client.delete(f"/tasks/{created['id']}")
        resp = client.get(f"/tasks/{created['id']}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_double_delete(self, client):
        """Eliminar dos veces la misma tarea; la segunda devuelve 404."""
        created = _create_task(client)
        client.delete(f"/tasks/{created['id']}")
        resp = client.delete(f"/tasks/{created['id']}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"
