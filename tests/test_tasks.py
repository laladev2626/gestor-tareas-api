# Tests para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor en memoria compartido entre hilos gracias a StaticPool
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


def test_update_task_rejects_short_title(client):
    """Verifica que PATCH /tasks/{id} devuelve 422 si el título tiene menos de 3 caracteres."""
    created = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "AB"})
    assert response.status_code == 422
    assert "title" in str(response.json()["detail"])


def test_update_task_accepts_valid_title(client):
    """Verifica que PATCH /tasks/{id} acepta un título con 3 o más caracteres."""
    created = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "ABC"})
    assert response.status_code == 200
    assert response.json()["title"] == "ABC"


def test_create_task_default_priority(client):
    """Verifica que POST /tasks/ asigna prioridad medium por defecto."""
    response = client.post("/tasks/", json={"title": "Sin prioridad explícita"})
    assert response.status_code == 201
    assert response.json()["priority"] == "medium"


def test_create_task_with_explicit_priority(client):
    """Verifica que POST /tasks/ acepta una prioridad explícita."""
    response = client.post(
        "/tasks/", json={"title": "Tarea urgente", "priority": "high"},
    )
    assert response.status_code == 201
    assert response.json()["priority"] == "high"


def test_create_task_invalid_priority(client):
    """Verifica que POST /tasks/ devuelve 422 con una prioridad no válida."""
    response = client.post(
        "/tasks/", json={"title": "Tarea", "priority": "urgent"},
    )
    assert response.status_code == 422
    assert "priority" in str(response.json()["detail"])


def test_update_task_priority(client):
    """Verifica que PATCH /tasks/{id} permite cambiar la prioridad."""
    created = client.post("/tasks/", json={"title": "Tarea"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"priority": "low"})
    assert response.status_code == 200
    assert response.json()["priority"] == "low"


def test_update_task_invalid_priority(client):
    """Verifica que PATCH /tasks/{id} devuelve 422 con una prioridad no válida."""
    created = client.post("/tasks/", json={"title": "Tarea"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"priority": "critical"})
    assert response.status_code == 422
    assert "priority" in str(response.json()["detail"])


def test_create_task_default_category(client):
    """Verifica que POST /tasks/ asigna categoría 'otro' por defecto."""
    response = client.post("/tasks/", json={"title": "Sin categoría explícita"})
    assert response.status_code == 201
    assert response.json()["category"] == "otro"


def test_create_task_with_explicit_category(client):
    """Verifica que POST /tasks/ acepta una categoría explícita."""
    response = client.post(
        "/tasks/", json={"title": "Tarea de trabajo", "category": "trabajo"},
    )
    assert response.status_code == 201
    assert response.json()["category"] == "trabajo"


def test_create_task_invalid_category(client):
    """Verifica que POST /tasks/ devuelve 422 con una categoría no válida."""
    response = client.post(
        "/tasks/", json={"title": "Tarea", "category": "finanzas"},
    )
    assert response.status_code == 422
    assert "category" in str(response.json()["detail"])


def test_update_task_category(client):
    """Verifica que PATCH /tasks/{id} permite cambiar la categoría."""
    created = client.post("/tasks/", json={"title": "Tarea"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"category": "personal"})
    assert response.status_code == 200
    assert response.json()["category"] == "personal"


def test_update_task_invalid_category(client):
    """Verifica que PATCH /tasks/{id} devuelve 422 con una categoría no válida."""
    created = client.post("/tasks/", json={"title": "Tarea"})
    task_id = created.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"category": "deportes"})
    assert response.status_code == 422
    assert "category" in str(response.json()["detail"])
