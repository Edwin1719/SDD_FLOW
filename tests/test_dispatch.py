"""Tests de envío de recordatorios (T7).

Criterios de T7: envío con consentimiento, sin consentimiento, reintento sin
duplicado y fallo tras agotar reintentos (RF-4, RF-5, RF-8, RF-10, RF-16).
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.sim_messaging import SimulatedMessaging
from app.db.repository import connect
from app.services.dispatch import dispatch_due_reminders

UTC = timezone.utc
NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
STARTS_AT = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)


def _seed(
    repo,
    *,
    has_consent: bool = True,
    status: str = "pending",
    opted_out: bool = False,
) -> int:
    phone = "+573001234567"
    repo.upsert_patient(phone, has_consent=has_consent, opted_out=opted_out)
    appointment_id = repo.create_appointment(
        event_id="evt-1",
        patient_name="Paciente",
        phone=phone,
        starts_at=STARTS_AT,
        status=status,
        updated_at=NOW,
    )
    repo.create_reminder(
        appointment_id=appointment_id,
        kind="R1",
        starts_at_snapshot=STARTS_AT,
        scheduled_for=NOW,
    )
    return appointment_id


def test_sends_with_consent(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    _seed(repo, has_consent=True)

    dispatch_due_reminders(repo, messaging, now=NOW)

    assert len(messaging.messages) == 1
    assert messaging.messages[0][0] == "+573001234567"

    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "reminder_sent"
    assert repo.list_reminders(appointment["id"])[0]["state"] == "sent"
    repo.close()


def test_skips_without_consent(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    _seed(repo, has_consent=False)

    dispatch_due_reminders(repo, messaging, now=NOW)

    assert len(messaging.messages) == 0
    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "no_consent"
    assert repo.list_reminders(appointment["id"])[0]["state"] == "skipped"
    repo.close()


def test_retry_sends_once(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    messaging.fail_next(1)  # falla solo el primer intento
    _seed(repo, has_consent=True)

    dispatch_due_reminders(repo, messaging, now=NOW)
    appointment = repo.get_appointment("evt-1")
    reminder = repo.list_reminders(appointment["id"])[0]
    assert reminder["state"] == "pending"
    assert reminder["attempts"] == 1
    assert len(messaging.messages) == 0

    dispatch_due_reminders(repo, messaging, now=NOW + timedelta(minutes=1))
    reminder = repo.list_reminders(appointment["id"])[0]
    assert reminder["state"] == "sent"
    assert len(messaging.messages) == 1  # un único mensaje total
    repo.close()


def test_fails_after_exhausting_retries(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    messaging.fail_always()
    _seed(repo, has_consent=True)

    dispatch_due_reminders(repo, messaging, now=NOW)  # intento 1
    dispatch_due_reminders(repo, messaging, now=NOW + timedelta(minutes=1))  # intento 2
    dispatch_due_reminders(repo, messaging, now=NOW + timedelta(minutes=6))  # intento 3

    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "send_error"
    reminder = repo.list_reminders(appointment["id"])[0]
    assert reminder["state"] == "failed"
    assert reminder["attempts"] == 3
    assert len(messaging.messages) == 0
    repo.close()


@pytest.mark.parametrize("status", ["cancelled_by_patient", "reschedule_requested"])
def test_skips_cancelled_or_rescheduled(tmp_path, status):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    _seed(repo, status=status)

    dispatch_due_reminders(repo, messaging, now=NOW)

    appointment = repo.get_appointment("evt-1")
    assert repo.list_reminders(appointment["id"])[0]["state"] == "skipped"
    assert messaging.messages == []
    repo.close()


def test_skips_opted_out_patient(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    _seed(repo, has_consent=True, opted_out=True)

    dispatch_due_reminders(repo, messaging, now=NOW)

    appointment = repo.get_appointment("evt-1")
    assert repo.list_reminders(appointment["id"])[0]["state"] == "skipped"
    assert messaging.messages == []
    repo.close()
