"""Tests web de lista de espera y espacios liberados (Spec 003)."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.config import Config

UTC = timezone.utc
NOW = datetime(2026, 11, 2, 15, 0, tzinfo=UTC)  # 10:00 en Bogotá
SLOT_START = datetime(2026, 11, 2, 20, 0, tzinfo=UTC)  # 15:00 en Bogotá
SLOT_END = SLOT_START + timedelta(minutes=30)


def _app(tmp_path, mode: str = "demo"):
    app = create_app(
        Config.from_env(
            {"MODE": mode, "DATABASE_PATH": str(tmp_path / "data" / "db.sqlite")}
        )
    )
    if hasattr(app.state.clock, "reset"):
        app.state.clock.reset(NOW)
    return app


def _slot(app):
    repo = app.state.repo
    return repo.create_freed_slot(
        event_id="evt-free",
        starts_at=SLOT_START,
        ends_at=SLOT_END,
        duration_estimated=False,
        source="cancelada",
        created_at=NOW,
    )


def _entry(app, name="Carla Méndez"):
    return next(
        e for e in app.state.repo.list_waitlist_entries() if e["patient_name"] == name
    )


def test_waitlist_page_and_entries(tmp_path):
    app = _app(tmp_path)
    client = TestClient(app)
    response = client.get("/lista-espera")
    assert response.status_code == 200
    assert "Lista de espera" in response.text
    assert "Carla Méndez" in response.text
    app.state.repo.close()


def test_create_waitlist_entry(tmp_path):
    app = _app(tmp_path)
    repo = app.state.repo
    client = TestClient(app)
    response = client.post(
        "/lista-espera/crear",
        data={
            "patient_name": "Nuevo Paciente",
            "phone": "+57 300 111 2233",
            "reason": "control",
            "days": ["0", "2"],
            "time_start": "09:00",
            "time_end": "12:00",
            "consent": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    entry = next(
        e for e in repo.list_waitlist_entries() if e["patient_name"] == "Nuevo Paciente"
    )
    assert entry["phone"] == "+573001112233"
    assert entry["status"] == "activa"
    assert repo.get_patient("+573001112233")["has_consent"] == 1
    repo.close()


def test_create_waitlist_rejects_invalid_phone(tmp_path):
    app = _app(tmp_path)
    client = TestClient(app)
    response = client.post(
        "/lista-espera/crear",
        data={
            "patient_name": "Sin Teléfono",
            "phone": "300 111 2233",
            "reason": "control",
            "days": [],
            "consent": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=phone" in response.headers["location"]
    app.state.repo.close()


def test_space_offer_accept_and_confirm(tmp_path):
    app = _app(tmp_path)
    repo = app.state.repo
    slot_id = _slot(app)
    entry = _entry(app)
    client = TestClient(app)

    page = client.get(f"/espacios/{slot_id}")
    assert page.status_code == 200
    assert "Ofrecer" in page.text

    offered = client.post(
        f"/espacios/{slot_id}/ofrecer",
        data={"entry_id": str(entry["id"])},
        follow_redirects=False,
    )
    assert offered.status_code == 303
    offer = repo.get_active_offer_for_slot(slot_id)
    assert offer is not None
    assert repo.get_freed_slot(slot_id)["status"] == "ofrecido"
    assert any(
        "se liberó un espacio" in body for _, body in app.state.messaging.messages
    )

    accepted = client.post(
        "/sim/offer/reply",
        data={"offer_id": str(offer["id"]), "action": "aceptar"},
        follow_redirects=False,
    )
    assert accepted.status_code == 303
    assert repo.get_freed_slot(slot_id)["status"] == "reservado_pendiente"

    confirmed = client.post(
        f"/espacios/{slot_id}/confirmar", follow_redirects=False
    )
    assert confirmed.status_code == 303
    assert repo.get_freed_slot(slot_id)["status"] == "recuperado"
    repo.close()


def test_panel_shows_freed_slot(tmp_path):
    app = _app(tmp_path)
    _slot(app)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Espacio liberado" in response.text
    assert "Ofrecer a lista" in response.text
    app.state.repo.close()


def test_agenda_cancel_creates_freed_slot(tmp_path):
    app = _app(tmp_path)
    repo = app.state.repo
    client = TestClient(app)
    assert repo.get_appointment("evt-1") is not None

    response = client.post(
        "/agenda/cancel", data={"event_id": "evt-1"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert repo.get_appointment("evt-1") is None
    assert len(repo.list_freed_slots()) >= 1
    repo.close()


def test_waitlist_routes_absent_in_real_mode(tmp_path):
    app = _app(tmp_path, mode="real")
    client = TestClient(app)
    assert client.get("/lista-espera").status_code == 404
    assert client.get("/espacios/1").status_code == 404
    app.state.repo.close()

def test_edit_waitlist_entry(tmp_path):
    app = _app(tmp_path)
    repo = app.state.repo
    entry = _entry(app)
    client = TestClient(app)

    response = client.post(
        "/lista-espera/editar",
        data={
            "entry_id": str(entry["id"]),
            "patient_name": "Carla Actualizada",
            "phone": entry["phone"],
            "reason": "control",
            "days": ["1", "3"],
            "time_start": "09:00",
            "time_end": "11:00",
            "consent": "1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    edited = repo.get_waitlist_entry(entry["id"])
    assert edited["patient_name"] == "Carla Actualizada"
    assert edited["reason"] == "control"
    assert edited["preferred_days"] == "1,3"
    assert edited["preferred_time_start"] == "09:00"
    repo.close()
