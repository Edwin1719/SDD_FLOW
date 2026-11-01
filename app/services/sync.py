"""Sincronización con el calendario (T6).

Lee los eventos del calendario y reconcilia las citas locales: crea las
nuevas, actualiza las movidas y elimina las canceladas (RF-1 a RF-3).
"""

from __future__ import annotations

from datetime import datetime, time, tzinfo

from app.db.repository import Repository
from app.domain.models import AppointmentStatus
from app.domain.scheduling import compute_reminders
from app.ports.calendar import CalendarPort


def sync_calendar(
    calendar: CalendarPort,
    repo: Repository,
    *,
    now: datetime,
    clinic_tz: tzinfo,
    window_start: time = time(8, 0),
    window_end: time = time(20, 0),
) -> None:
    """Reconcilia las citas locales con los eventos del calendario.

    Si la lectura del calendario falla, la excepción se propaga y no se
    modifica ni cancela ninguna cita local (regla de no pérdida de datos).
    """
    events, _token = calendar.list_events()
    event_ids = {event.event_id for event in events}

    for event in events:
        status = (
            AppointmentStatus.NO_PHONE
            if event.phone is None
            else AppointmentStatus.PENDING
        )
        existing = repo.get_appointment(event.event_id)

        if existing is None:
            appointment_id = repo.create_appointment(
                event_id=event.event_id,
                patient_name=event.patient_name,
                phone=event.phone,
                starts_at=event.starts_at,
                status=status.value,
                updated_at=now,
            )
        else:
            appointment_id = existing["id"]
            stored_starts = datetime.fromisoformat(existing["starts_at"])
            if stored_starts != event.starts_at:
                # Movida (RF-3): descartar pendientes y reiniciar en Pendiente.
                repo.skip_pending_reminders(appointment_id)
                repo.update_appointment(
                    appointment_id,
                    starts_at=event.starts_at,
                    status=status.value,
                    updated_at=now,
                )
            else:
                continue  # sin cambios

        if event.phone is not None:
            _schedule_reminders(
                repo,
                appointment_id,
                event.starts_at,
                now,
                clinic_tz,
                window_start,
                window_end,
            )

    # Eliminar las citas cuyo evento ya no está en el calendario (RF-3).
    for appointment in repo.list_appointments():
        if appointment["event_id"] not in event_ids:
            repo.delete_appointment(appointment["id"])


def _schedule_reminders(
    repo: Repository,
    appointment_id: int,
    starts_at: datetime,
    now: datetime,
    clinic_tz: tzinfo,
    window_start: time,
    window_end: time,
) -> None:
    for reminder in compute_reminders(
        starts_at=starts_at,
        now=now,
        clinic_tz=clinic_tz,
        window_start=window_start,
        window_end=window_end,
    ):
        repo.create_reminder(
            appointment_id=appointment_id,
            kind=reminder.kind.value,
            starts_at_snapshot=starts_at,
            scheduled_for=reminder.scheduled_for,
        )
