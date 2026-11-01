"""Datos de ejemplo y restauración del modo demo (constitución 13)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo

from app.adapters.clocks import SimulatedClock
from app.adapters.fake_calendar import FakeCalendar
from app.adapters.sim_messaging import SimulatedMessaging
from app.db.repository import Repository
from app.domain.phone import extract_phone
from app.ports.calendar import CalendarEvent
from app.services.planner import run_cycle


def reset_demo(
    repo: Repository,
    calendar: FakeCalendar,
    clock: SimulatedClock,
    messaging: SimulatedMessaging,
    *,
    clinic_tz: tzinfo,
) -> None:
    """Restaura la demo: datos ficticios y una sincronización inicial."""
    now = datetime.now(timezone.utc)
    clock.reset(now)
    messaging.clear()
    repo.clear_all()

    # Pacientes ficticios (consentimiento previo, S4).
    repo.upsert_patient("+573001234567", has_consent=True)  # Ana
    repo.upsert_patient("+573002345678", has_consent=True)  # Luis
    repo.upsert_patient(
        "+573003456789", has_consent=False
    )  # María (sin consentimiento)

    # Citas de ejemplo (el teléfono se extrae de la línea `Tel:`).
    calendar.events = [
        CalendarEvent(
            event_id="evt-1",
            patient_name="Ana Gómez",
            starts_at=now + timedelta(days=3),
            phone=extract_phone("Tel: +57 300 123 4567"),
        ),
        CalendarEvent(
            event_id="evt-2",
            patient_name="Luis Pérez",
            starts_at=now + timedelta(days=1, hours=6),
            phone=extract_phone("Tel: +57 300 234 5678"),
        ),
        CalendarEvent(
            event_id="evt-3",
            patient_name="María López",
            starts_at=now + timedelta(days=2),
            phone=extract_phone("Tel: +57 300 345 6789"),
        ),
        CalendarEvent(
            event_id="evt-4",
            patient_name="Pedro Ruiz",
            starts_at=now + timedelta(days=2, hours=2),
            phone=None,  # sin teléfono
        ),
    ]

    run_cycle(calendar, repo, messaging, clock, clinic_tz=clinic_tz)
