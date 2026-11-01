"""Tests de respuestas del paciente (T8).

Criterios de T8: cada botón, baja con «BAJA», respuesta posterior a la cita y
respuesta a una fecha ya cambiada (RF-9, RF-11 a RF-14).
"""

from datetime import datetime, timedelta, timezone

from app.adapters.sim_messaging import SimulatedMessaging
from app.db.repository import connect
from app.domain.models import ReplyAction
from app.services.replies import apply_button_reply, apply_optout

UTC = timezone.utc
STARTS_AT = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
BEFORE = STARTS_AT - timedelta(days=1)
LATE = STARTS_AT + timedelta(hours=1)

PHONE = "+573001234567"


def _seed_appointment(repo, *, status: str = "reminder_sent") -> int:
    repo.upsert_patient(PHONE, has_consent=True)
    return repo.create_appointment(
        event_id="evt-1",
        patient_name="Paciente",
        phone=PHONE,
        starts_at=STARTS_AT,
        status=status,
        updated_at=BEFORE,
    )


def test_confirm_applies_and_replies(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    appointment_id = _seed_appointment(repo)

    apply_button_reply(
        repo,
        messaging,
        appointment_id=appointment_id,
        action=ReplyAction.CONFIRM,
        original_starts_at=STARTS_AT,
        received_at=BEFORE,
    )

    assert repo.get_appointment_by_id(appointment_id)["status"] == "confirmed"
    assert repo.list_replies(appointment_id)[0]["applied"] == 1
    assert messaging.messages == [(PHONE, "¡Gracias! Te esperamos.")]
    repo.close()


def test_reschedule_applies_and_replies(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    appointment_id = _seed_appointment(repo)

    apply_button_reply(
        repo,
        messaging,
        appointment_id=appointment_id,
        action=ReplyAction.RESCHEDULE,
        original_starts_at=STARTS_AT,
        received_at=BEFORE,
    )

    assert (
        repo.get_appointment_by_id(appointment_id)["status"] == "reschedule_requested"
    )
    assert repo.list_replies(appointment_id)[0]["applied"] == 1
    assert messaging.messages == [
        (PHONE, "Entendido. La asistente te contactará para elegir una nueva fecha.")
    ]
    repo.close()


def test_cancel_applies_and_replies(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    appointment_id = _seed_appointment(repo)

    apply_button_reply(
        repo,
        messaging,
        appointment_id=appointment_id,
        action=ReplyAction.CANCEL,
        original_starts_at=STARTS_AT,
        received_at=BEFORE,
    )

    assert (
        repo.get_appointment_by_id(appointment_id)["status"] == "cancelled_by_patient"
    )
    assert repo.list_replies(appointment_id)[0]["applied"] == 1
    assert messaging.messages == [
        (PHONE, "Listo, cancelamos tu cita. Si quieres agendar otra, escríbenos.")
    ]
    repo.close()


def test_optout_discards_pending_reminders(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient(PHONE, has_consent=True)
    first = repo.create_appointment(
        event_id="evt-1",
        patient_name="Paciente",
        phone=PHONE,
        starts_at=STARTS_AT,
        status="reminder_sent",
        updated_at=BEFORE,
    )
    second = repo.create_appointment(
        event_id="evt-2",
        patient_name="Paciente",
        phone=PHONE,
        starts_at=STARTS_AT,
        status="reminder_sent",
        updated_at=BEFORE,
    )
    repo.create_reminder(
        appointment_id=first,
        kind="R1",
        starts_at_snapshot=STARTS_AT,
        scheduled_for=BEFORE,
    )
    repo.create_reminder(
        appointment_id=second,
        kind="R1",
        starts_at_snapshot=STARTS_AT,
        scheduled_for=BEFORE,
    )

    apply_optout(repo, appointment_id=first, received_at=BEFORE)

    assert repo.get_patient(PHONE)["opted_out"] == 1
    assert all(r["state"] == "skipped" for r in repo.list_reminders(first))
    assert all(r["state"] == "skipped" for r in repo.list_reminders(second))
    repo.close()


def test_late_reply_ignored(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    appointment_id = _seed_appointment(repo)

    apply_button_reply(
        repo,
        messaging,
        appointment_id=appointment_id,
        action=ReplyAction.CONFIRM,
        original_starts_at=STARTS_AT,
        received_at=LATE,
    )

    assert repo.get_appointment_by_id(appointment_id)["status"] == "reminder_sent"
    assert repo.list_replies(appointment_id)[0]["applied"] == 0
    assert messaging.messages == []
    repo.close()


def test_reply_to_changed_date_ignored(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    appointment_id = _seed_appointment(repo)

    apply_button_reply(
        repo,
        messaging,
        appointment_id=appointment_id,
        action=ReplyAction.CONFIRM,
        original_starts_at=STARTS_AT + timedelta(days=1),  # fecha ya no vigente
        received_at=BEFORE,
    )

    assert repo.get_appointment_by_id(appointment_id)["status"] == "reminder_sent"
    assert repo.list_replies(appointment_id)[0]["applied"] == 0
    assert messaging.messages == []
    repo.close()
