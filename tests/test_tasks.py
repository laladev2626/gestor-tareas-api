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



def test_create_task_with_description(client):
    """Verifica que POST /tasks/ acepta una descripción válida."""
    response = client.post(
        "/tasks/",
        json={"title": "Tarea con desc", "description": "Descripción de ejemplo"},
    )
    assert response.status_code == 201
    assert response.json()["description"] == "Descripción de ejemplo"


def test_create_task_without_description(client):
    """Verifica que POST /tasks/ permite omitir la descripción."""
    response = client.post("/tasks/", json={"title": "Sin descripción"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_task_rejects_description_over_500(client):
    """Verifica que POST /tasks/ devuelve 422 si la descripción supera 500 caracteres."""
    long_desc = "a" * 501
    response = client.post(
        "/tasks/", json={"title": "Tarea larga", "description": long_desc},
    )
    assert response.status_code == 422
    assert "description" in str(response.json()["detail"])


def test_create_task_accepts_description_of_500(client):
    """Verifica que POST /tasks/ acepta una descripción de exactamente 500 caracteres."""
    desc_500 = "a" * 500
    response = client.post(
        "/tasks/", json={"title": "Tarea límite", "description": desc_500},
    )
    assert response.status_code == 201
    assert response.json()["description"] == desc_500


def test_update_task_rejects_description_over_500(client):
    """Verifica que PATCH /tasks/{id} devuelve 422 si la descripción supera 500 caracteres."""
    created = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = created.json()["id"]

    long_desc = "a" * 501
    response = client.patch(
        f"/tasks/{task_id}", json={"description": long_desc},
    )
    assert response.status_code == 422
    assert "description" in str(response.json()["detail"])


def test_update_task_accepts_description_of_500(client):
    """Verifica que PATCH /tasks/{id} acepta una descripción de exactamente 500 caracteres."""
    created = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = created.json()["id"]

    desc_500 = "a" * 500
    response = client.patch(
        f"/tasks/{task_id}", json={"description": desc_500},
    )
    assert response.status_code == 200
    assert response.json()["description"] == desc_500


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
