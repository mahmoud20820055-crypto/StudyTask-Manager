import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    app = create_app(database_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_and_list_task(client):
    response = client.post(
        "/api/tasks",
        json={"title": "OS Lab report", "course": "OS Lab", "priority": "high", "due_date": "2026-12-01"},
    )
    assert response.status_code == 201
    assert response.get_json()["title"] == "OS Lab report"

    tasks = client.get("/api/tasks").get_json()
    assert len(tasks) == 1
    assert tasks[0]["done"] is False


def test_title_is_required(client):
    response = client.post("/api/tasks", json={"course": "OS Lab"})
    assert response.status_code == 400


def test_invalid_priority_rejected(client):
    response = client.post("/api/tasks", json={"title": "x", "priority": "urgent"})
    assert response.status_code == 400


def test_update_delete_and_stats(client):
    task_id = client.post("/api/tasks", json={"title": "Read chapter 5"}).get_json()["id"]

    response = client.patch(f"/api/tasks/{task_id}", json={"done": True})
    assert response.get_json()["done"] is True
    assert client.get("/api/stats").get_json() == {"total": 1, "done": 1, "pending": 0}

    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.delete(f"/api/tasks/{task_id}").status_code == 404
