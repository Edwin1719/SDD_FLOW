"""Tests de la agenda simulada (T20, CA-7)."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.config import Config

UTC = timezone.utc


def _config(tmp_path, mode: str = "demo") -> Config:
    return Config.from_env(
        {"MODE": mode, "DATABASE_PATH": str(tmp_path / "data" / "db.sqlite")}
    )


def test_agenda_page_renders(tmp_path):
    app = create_app(_config(tmp_path))
    client = TestClient(app)
    response = client.get("/agenda")
    assert response.status_code == 200
    assert "Agenda" in response.text
    assert "Demo" in response.text
    app.state.repo.close()


def test_create_appointment(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)

    future = datetime.now(UTC) + timedelta(days=5)
    client.post(
        "/agenda/create",
        data={
            "patient_name": "Nuevo Paciente",
            "phone": "+57 300 999 0000",
            "date": future.strftime("%Y-%m-%d"),
            "time": future.strftime("%H:%M"),
        },
    )

    appointment = repo.get_appointment("evt-1001")
    assert appointment is not None
    assert appointment["patient_name"] == "Nuevo Paciente"
    assert appointment["phone"] == "+573009990000"
    assert appointment["status"] == "pending"
    repo.close()


def test_move_appointment_discards_pending(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)

    original = repo.get_appointment("evt-1")
    new_start = datetime.fromisoformat(original["starts_at"]) + timedelta(days=1)
    local = new_start.astimezone(app.state.clinic_tz)

    client.post(
        "/agenda/move",
        data={
            "event_id": "evt-1",
            "date": local.strftime("%Y-%m-%d"),
            "time": local.strftime("%H:%M"),
        },
    )

    moved = repo.get_appointment("evt-1")
    assert moved is not None
    assert moved["status"] == "pending"
    assert datetime.fromisoformat(moved["starts_at"]) != datetime.fromisoformat(
        original["starts_at"]
    )
    states = {r["state"] for r in repo.list_reminders(moved["id"])}
    assert states <= {"pending", "skipped"}
    repo.close()


def test_cancel_appointment_removes_it(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)

    assert repo.get_appointment("evt-2") is not None
    client.post("/agenda/cancel", data={"event_id": "evt-2"})
    assert repo.get_appointment("evt-2") is None
    repo.close()


def test_agenda_routes_absent_in_real_mode(tmp_path):
    app = create_app(_config(tmp_path, mode="real"))
    client = TestClient(app)
    assert client.get("/agenda").status_code == 404
    assert client.post("/agenda/create", data={}).status_code == 404
    app.state.repo.close()
