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


def _local_time(now: datetime, clinic_tz: tzinfo, days: int, hour: int) -> datetime:
    """Devuelve una hora local del consultorio convertida a UTC."""
    local_day = now.astimezone(clinic_tz).date() + timedelta(days=days)
    local = datetime(
        local_day.year, local_day.month, local_day.day, hour, 0, tzinfo=clinic_tz
    )
    return local.astimezone(timezone.utc)


def reset_demo(
    repo: Repository,
    calendar: FakeCalendar,
    clock: SimulatedClock,
    messaging: SimulatedMessaging,
    *,
    clinic_tz: tzinfo,
) -> None:
    """Restaura la demo con citas en horario del consultorio (hora local)."""
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

    # Citas de ejemplo en horario del consultorio (09:00, 10:00, 15:00, 16:00).
    ana_start = _local_time(now, clinic_tz, 3, 9)
    luis_start = _local_time(now, clinic_tz, 3, 10)
    maria_start = _local_time(now, clinic_tz, 3, 15)
    pedro_start = _local_time(now, clinic_tz, 3, 16)
    calendar.events = [
        CalendarEvent(
            event_id="evt-1",
            patient_name="Ana Gómez",
            starts_at=ana_start,
            phone=extract_phone("Tel: +57 300 123 4567"),
            ends_at=ana_start + timedelta(minutes=30),
        ),
        CalendarEvent(
            event_id="evt-2",
            patient_name="Luis Pérez",
            starts_at=luis_start,
            phone=extract_phone("Tel: +57 300 234 5678"),
            ends_at=luis_start + timedelta(minutes=30),
        ),
        CalendarEvent(
            event_id="evt-3",
            patient_name="María López",
            starts_at=maria_start,
            phone=extract_phone("Tel: +57 300 345 6789"),
            ends_at=maria_start + timedelta(minutes=45),
        ),
        CalendarEvent(
            event_id="evt-4",
            patient_name="Pedro Ruiz",
            starts_at=pedro_start,
            phone=None,  # sin teléfono
            ends_at=pedro_start + timedelta(minutes=30),
        ),
    ]

    # Lista de espera de ejemplo.
    repo.upsert_patient("+573004567890", has_consent=True)  # Carla
    repo.upsert_patient("+573005678901", has_consent=True)  # Jorge
    repo.upsert_patient("+573006789012", has_consent=False)  # Lucía
    repo.create_waitlist_entry(
        patient_name="Carla Méndez",
        phone="+573004567890",
        reason="limpieza",
        preferred_days="0,2,4",
        preferred_time_start="08:00",
        preferred_time_end="12:00",
        status="activa",
        created_at=now,
    )
    repo.create_waitlist_entry(
        patient_name="Jorge Salazar",
        phone="+573005678901",
        reason="consulta",
        preferred_days="1,3",
        preferred_time_start="14:00",
        preferred_time_end="18:00",
        status="activa",
        created_at=now,
    )
    repo.create_waitlist_entry(
        patient_name="Lucía Torres",
        phone="+573006789012",
        reason="control",
        preferred_days="",
        preferred_time_start=None,
        preferred_time_end=None,
        status="sin_consentimiento",
        created_at=now,
    )

    run_cycle(calendar, repo, messaging, clock, clinic_tz=clinic_tz)
