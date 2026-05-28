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
