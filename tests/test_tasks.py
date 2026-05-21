# Tests para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app


# Motor en memoria aislado para cada sesión de tests
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine_test)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# ---------- GET /tasks/status/{status} ----------

def test_list_tasks_by_status_returns_filtered_results(client):
    """Happy path: solo devuelve las tareas con el estado solicitado."""
    client.post("/tasks/", json={"title": "Tarea pendiente"})
    client.post("/tasks/", json={"title": "Tarea en progreso", "status": "in_progress"})
    client.post("/tasks/", json={"title": "Tarea hecha", "status": "done"})

    response = client.get("/tasks/status/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tarea pendiente"
    assert data[0]["status"] == "pending"


def test_list_tasks_by_status_invalid_status(client):
    """Caso de error: un estado no válido debe devolver 422."""
    response = client.get("/tasks/status/invalid_status")
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
