# Tests para el endpoint DELETE /tasks/ (eliminación masiva de tareas)

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


def test_delete_all_tasks_removes_every_task(client):
    """Crea varias tareas y verifica que DELETE /tasks/ las elimina todas."""
    client.post("/tasks/", json={"title": "Tarea 1"})
    client.post("/tasks/", json={"title": "Tarea 2"})
    client.post("/tasks/", json={"title": "Tarea 3"})

    response = client.delete("/tasks/")
    assert response.status_code == 204

    listing = client.get("/tasks/")
    assert listing.status_code == 200
    assert listing.json() == []


def test_delete_all_tasks_on_empty_database(client):
    """Verifica que DELETE /tasks/ devuelve 204 incluso sin tareas."""
    response = client.delete("/tasks/")
    assert response.status_code == 204

    listing = client.get("/tasks/")
    assert listing.status_code == 200
    assert listing.json() == []
