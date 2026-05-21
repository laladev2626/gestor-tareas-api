# Tests para el endpoint PATCH /tasks/{id} — validación de tareas completadas

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

import pytest

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

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
    Base.metadata.drop_all(bind=engine)


def _create_task(client, **kwargs):
    payload = {"title": "Tarea de prueba"}
    payload.update(kwargs)
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_update_task_done_returns_400(client):
    task = _create_task(client, status="done")

    response = client.patch(f"/tasks/{task['id']}", json={"title": "Nuevo título"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a completed task"


def test_update_task_done_status_change_returns_400(client):
    task = _create_task(client, status="done")

    response = client.patch(f"/tasks/{task['id']}", json={"status": "pending"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a completed task"


def test_update_task_pending_succeeds(client):
    task = _create_task(client, status="pending")

    response = client.patch(f"/tasks/{task['id']}", json={"title": "Título actualizado"})

    assert response.status_code == 200
    assert response.json()["title"] == "Título actualizado"


def test_update_task_in_progress_succeeds(client):
    task = _create_task(client, status="in_progress")

    response = client.patch(f"/tasks/{task['id']}", json={"status": "done"})

    assert response.status_code == 200
    assert response.json()["status"] == "done"
