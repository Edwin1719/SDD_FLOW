"""Pruebas de aceptación CA-1 a CA-5 (T13).

CA-8 (panel sin grilla) y CA-9 (edición de teléfono) se cubren en
`test_panel.py` y `test_agenda.py`. Aquí se recorre el flujo completo en modo
demo: sincronización, envío escalonado, respuestas, Sin confirmar y fallos.
"""

from datetime import datetime, timezone

from app.app_factory import create_app
from app.config import Config
from app.domain.models import ReplyAction
from app.ports.calendar import CalendarEvent
from app.services.planner import run_cycle
from app.services.replies import apply_button_reply
from app.web.routes import ATTENTION_STATES

UTC = timezone.utc
NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
STARTS_AT = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)  # +3 días
PHONE = "+573001234567"


def _demo(tmp_path):
    config = Config.from_env(
        {"MODE": "demo", "DATABASE_PATH": str(tmp_path / "data" / "db.sqlite")}
    )
    app = create_app(config)
    repo = app.state.repo
    calendar = app.state.calendar
    clock = app.state.clock
    messaging = app.state.messaging

    clock.reset(NOW)
    repo.clear_all()
    repo.upsert_patient(PHONE, has_consent=True)
    calendar.events = [
        CalendarEvent(
            event_id="evt-1", patient_name="Paciente", starts_at=STARTS_AT, phone=PHONE
        )
    ]
    messaging.clear()
    run_cycle(calendar, repo, messaging, clock, clinic_tz=UTC)
    return app, repo, calendar, clock, messaging


def _cycle(calendar, repo, messaging, clock):
    run_cycle(calendar, repo, messaging, clock, clinic_tz=UTC)


def _sent(repo, appointment_id):
    return {
        r["kind"] for r in repo.list_reminders(appointment_id) if r["state"] == "sent"
    }


def _reply(repo, messaging, clock, action):
    appointment = repo.get_appointment("evt-1")
    apply_button_reply(
        repo,
        messaging,
        appointment_id=appointment["id"],
        action=action,
        original_starts_at=STARTS_AT,
        received_at=clock.now(),
    )


def test_ca1_staggered_reminders(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)
    appointment = repo.get_appointment("evt-1")

    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R1
    assert _sent(repo, appointment["id"]) == {"R1"}

    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R2
    assert _sent(repo, appointment["id"]) == {"R1", "R2"}

    # Sin duplicados (RF-10): un mensaje por recordatorio.
    assert len(messaging.messages) == 2
    repo.close()


def test_ca2_one_tap_confirmation(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)
    appointment = repo.get_appointment("evt-1")

    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R1 enviado

    _reply(repo, messaging, clock, ReplyAction.CONFIRM)
    assert repo.get_appointment("evt-1")["status"] == "confirmed"
    assert any(body == "¡Gracias! Te esperamos." for _to, body in messaging.messages)

    # La confirmación no cancela el recordatorio de 24 h (RF-11).
    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)
    assert _sent(repo, appointment["id"]) == {"R1", "R2"}
    repo.close()


def test_ca3_reschedule_notifies(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)
    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)

    _reply(repo, messaging, clock, ReplyAction.RESCHEDULE)
    status = repo.get_appointment("evt-1")["status"]
    assert status == "reschedule_requested"
    assert status in ATTENTION_STATES
    repo.close()


def test_ca3_cancel_notifies(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)
    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)

    _reply(repo, messaging, clock, ReplyAction.CANCEL)
    status = repo.get_appointment("evt-1")["status"]
    assert status == "cancelled_by_patient"
    assert status in ATTENTION_STATES
    repo.close()


def test_ca4_no_response_unconfirmed(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)

    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R1
    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R2
    clock.advance(hours=3)
    _cycle(calendar, repo, messaging, clock)  # 3 h tras R2

    status = repo.get_appointment("evt-1")["status"]
    assert status == "unconfirmed"
    assert status in ATTENTION_STATES
    repo.close()


def test_ca4_confirmed_stays_confirmed(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)

    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R1
    _reply(repo, messaging, clock, ReplyAction.CONFIRM)

    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # R2
    clock.advance(hours=3)
    _cycle(calendar, repo, messaging, clock)

    assert repo.get_appointment("evt-1")["status"] == "confirmed"
    repo.close()


def test_ca5_failure_visible(tmp_path):
    _app, repo, calendar, clock, messaging = _demo(tmp_path)

    messaging.fail_always()
    clock.advance(hours=24)
    _cycle(calendar, repo, messaging, clock)  # intento 1
    clock.advance(minutes=1)
    _cycle(calendar, repo, messaging, clock)  # intento 2
    clock.advance(minutes=5)
    _cycle(calendar, repo, messaging, clock)  # intento 3

    status = repo.get_appointment("evt-1")["status"]
    assert status == "send_error"
    assert status in ATTENTION_STATES
    repo.close()
