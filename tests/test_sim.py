"""Tests del simulador del modo demo (T12)."""

from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.config import Config


def _config(tmp_path, mode: str = "demo") -> Config:
    return Config.from_env(
        {"MODE": mode, "DATABASE_PATH": str(tmp_path / "data" / "db.sqlite")}
    )


def test_sim_page_renders(tmp_path):
    app = create_app(_config(tmp_path))
    client = TestClient(app)
    response = client.get("/sim")
    assert response.status_code == 200
    assert "Demo" in response.text
    app.state.repo.close()


def test_reply_as_patient(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)
    appointment = repo.get_appointment("evt-1")

    client.post(
        "/sim/reply",
        data={
            "appointment_id": str(appointment["id"]),
            "starts_at": appointment["starts_at"],
            "action": "confirm",
        },
    )

    assert repo.get_appointment("evt-1")["status"] == "confirmed"
    repo.close()


def test_panel_reply_applies_and_redirects(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)
    appointment = repo.get_appointment("evt-1")

    response = client.post(
        "/panel/reply",
        data={
            "appointment_id": str(appointment["id"]),
            "starts_at": appointment["starts_at"],
            "action": "confirm",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert repo.get_appointment("evt-1")["status"] == "confirmed"
    repo.close()


def test_clock_advance_triggers_reminders(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)
    appointment = repo.get_appointment("evt-1")
    assert all(r["state"] == "pending" for r in repo.list_reminders(appointment["id"]))

    client.post("/sim/clock/advance", data={"hours": "48"})

    reminders = repo.list_reminders(appointment["id"])
    assert any(r["kind"] == "R1" and r["state"] == "sent" for r in reminders)
    repo.close()


def test_fail_next_send_causes_retry(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)

    client.post("/sim/fail-next-send")
    client.post("/sim/clock/advance", data={"hours": "48"})

    appointment = repo.get_appointment("evt-1")
    reminders = repo.list_reminders(appointment["id"])
    r1 = next(r for r in reminders if r["kind"] == "R1")
    assert r1["state"] == "pending"
    assert r1["attempts"] == 1
    repo.close()


def test_reset_restores_data(tmp_path):
    app = create_app(_config(tmp_path))
    repo = app.state.repo
    client = TestClient(app)
    appointment = repo.get_appointment("evt-1")
    client.post(
        "/sim/reply",
        data={
            "appointment_id": str(appointment["id"]),
            "starts_at": appointment["starts_at"],
            "action": "confirm",
        },
    )
    assert repo.get_appointment("evt-1")["status"] == "confirmed"

    client.post("/sim/reset")
    assert repo.get_appointment("evt-1")["status"] == "pending"
    repo.close()


def test_sim_routes_absent_in_real_mode(tmp_path):
    app = create_app(_config(tmp_path, mode="real"))
    client = TestClient(app)
    assert client.get("/sim").status_code == 404
    assert client.post("/sim/clock/advance", data={"hours": "24"}).status_code == 404
    app.state.repo.close()
