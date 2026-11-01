"""Tests del panel de la asistente (T11).

Criterio de T11: el panel muestra cada estado con texto y tono (RF-17).
"""

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.repository import connect
from app.adapters.clocks import SystemClock
from app.web.routes import router

UTC = timezone.utc

STATES = [
    ("pending", "Pendiente", "neutro"),
    ("reminder_sent", "Recordatorio enviado", "neutro"),
    ("confirmed", "Confirmada", "exito"),
    ("reschedule_requested", "Reprogramación solicitada", "atencion"),
    ("cancelled_by_patient", "Cancelada por paciente", "morado"),
    ("unconfirmed", "Sin confirmar", "atencion"),
    ("send_error", "Error de envío", "peligro"),
    ("no_consent", "Sin consentimiento", "neutro"),
    ("no_phone", "Sin teléfono", "atencion"),
]


def _make_app(repo) -> FastAPI:
    app = FastAPI()
    app.state.repo = repo
    app.state.clinic_tz = UTC
    app.state.clock = SystemClock()
    app.state.mode = "demo"
    app.include_router(router)
    return app


def test_panel_renders_every_state_with_text_and_tone(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    future = datetime.now(UTC) + timedelta(days=1)
    for i, (status, _label, _tone) in enumerate(STATES):
        repo.create_appointment(
            event_id=f"evt-{i}",
            patient_name=f"Paciente {i}",
            phone="+573001234567",
            starts_at=future + timedelta(hours=i),
            status=status,
            updated_at=datetime.now(UTC),
        )

    client = TestClient(_make_app(repo))
    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    for _status, label, tone in STATES:
        assert label in html
        assert f"estado-{tone}" in html
    repo.close()


def test_panel_empty_state(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    client = TestClient(_make_app(repo))
    response = client.get("/")

    assert response.status_code == 200
    assert "Hoy no hay citas." in response.text
    repo.close()
