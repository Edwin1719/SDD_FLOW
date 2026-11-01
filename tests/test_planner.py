"""Tests del planificador (T9).

Criterio de T9: adelantar el reloj simulado y comprobar R1, R2 y Sin confirmar
sin esperar (RF-4, RF-5, RF-15).
"""

from datetime import datetime, timedelta, timezone

from app.adapters.clocks import SimulatedClock
from app.adapters.fake_calendar import FakeCalendar
from app.adapters.sim_messaging import SimulatedMessaging
from app.db.repository import connect
from app.ports.calendar import CalendarEvent
from app.services.planner import run_cycle

UTC = timezone.utc
STARTS_AT = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
PHONE = "+573001234567"


def test_planner_sends_r1_r2_and_marks_unconfirmed(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient(PHONE, has_consent=True)
    messaging = SimulatedMessaging()
    calendar = FakeCalendar(
        [
            CalendarEvent(
                event_id="evt-1",
                patient_name="Paciente",
                starts_at=STARTS_AT,
                phone=PHONE,
            )
        ]
    )
    clock = SimulatedClock(start=STARTS_AT - timedelta(days=3))

    # Ciclo 1: sincroniza y programa R1/R2; nada enviado aún.
    run_cycle(calendar, repo, messaging, clock, clinic_tz=UTC)
    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "pending"
    assert messaging.messages == []

    # Avanzar hasta R1 (-48 h): se envía R1.
    clock.advance(hours=24)
    run_cycle(calendar, repo, messaging, clock, clinic_tz=UTC)
    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "reminder_sent"
    reminders = repo.list_reminders(appointment["id"])
    assert any(r["kind"] == "R1" and r["state"] == "sent" for r in reminders)
    assert len(messaging.messages) == 1

    # Avanzar hasta R2 (-24 h): se envía R2.
    clock.advance(hours=24)
    run_cycle(calendar, repo, messaging, clock, clinic_tz=UTC)
    reminders = repo.list_reminders(appointment["id"])
    assert any(r["kind"] == "R2" and r["state"] == "sent" for r in reminders)
    assert len(messaging.messages) == 2

    # Avanzar 3 h tras R2: pasa a Sin confirmar.
    clock.advance(hours=3)
    run_cycle(calendar, repo, messaging, clock, clinic_tz=UTC)
    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "unconfirmed"
    repo.close()
