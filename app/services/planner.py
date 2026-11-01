"""Planificador: sincroniza, envía y marca Sin confirmar (T9)."""

from __future__ import annotations

from datetime import datetime, time, timedelta, tzinfo

from app.db.repository import Repository
from app.domain.models import Appointment, AppointmentStatus
from app.domain.rules import mark_unconfirmed as _mark_unconfirmed
from app.ports.calendar import CalendarPort
from app.ports.clock import ClockPort
from app.ports.messaging import MessagingPort
from app.services.dispatch import dispatch_due_reminders
from app.services.sync import sync_calendar


def run_cycle(
    calendar: CalendarPort,
    repo: Repository,
    messaging: MessagingPort,
    clock: ClockPort,
    *,
    clinic_tz: tzinfo,
    window_start: time = time(8, 0),
    window_end: time = time(20, 0),
    unconfirmed_after_hours: int = 3,
) -> None:
    """Un ciclo: sincroniza el calendario, envía lo pendiente y marca Sin confirmar."""
    now = clock.now()
    sync_calendar(
        calendar,
        repo,
        now=now,
        clinic_tz=clinic_tz,
        window_start=window_start,
        window_end=window_end,
    )
    dispatch_due_reminders(repo, messaging, now=now)
    _mark_unconfirmed_due(
        repo, now=now, unconfirmed_after_hours=unconfirmed_after_hours
    )


def _mark_unconfirmed_due(
    repo: Repository, *, now: datetime, unconfirmed_after_hours: int
) -> None:
    """Marca Sin confirmar las citas con R2 enviado hace más de N horas (RF-15)."""
    cutoff = now - timedelta(hours=unconfirmed_after_hours)
    for row in repo.list_appointments_with_r2_sent_before(cutoff):
        appointment = Appointment(
            event_id=row["event_id"],
            patient_name=row["patient_name"],
            phone=row["phone"],
            starts_at=datetime.fromisoformat(row["starts_at"]),
            status=AppointmentStatus(row["status"]),
        )
        updated = _mark_unconfirmed(appointment)
        if updated.status != appointment.status:
            repo.update_appointment_status(row["id"], updated.status.value, now)
