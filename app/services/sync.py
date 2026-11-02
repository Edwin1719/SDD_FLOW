"""Sincronización con el calendario (T6).

Lee los eventos del calendario y reconcilia las citas locales: crea las
nuevas, actualiza las movidas y elimina las canceladas (RF-1 a RF-3).
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, tzinfo

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
    default_duration_minutes: int = 30,
) -> None:
    """Reconcilia las citas locales con los eventos del calendario.

    Si la lectura del calendario falla, la excepción se propaga y no se
    modifica ni cancela ninguna cita local (regla de no pérdida de datos).
    """
    events, _token = calendar.list_events()
    event_ids = {event.event_id for event in events}

    for event in events:
        existing = repo.get_appointment(event.event_id)

        ends_at = event.ends_at

        if existing is None:
            status = _status_for(event, repo)
            appointment_id = repo.create_appointment(
                event_id=event.event_id,
                patient_name=event.patient_name,
                phone=event.phone,
                starts_at=event.starts_at,
                ends_at=ends_at,
                status=status.value,
                updated_at=now,
            )
            should_schedule = True
        else:
            appointment_id = existing["id"]
            stored_starts = datetime.fromisoformat(existing["starts_at"])
            time_changed = stored_starts != event.starts_at
            name_changed = existing["patient_name"] != event.patient_name
            phone_changed = existing["phone"] != event.phone
            ends_changed = existing["ends_at"] != (
                ends_at.isoformat() if ends_at is not None else None
            )

            if not (time_changed or name_changed or phone_changed or ends_changed):
                continue  # sin cambios

            status = existing["status"]
            if time_changed:
                # Movida (RF-3): liberar el espacio anterior y reiniciar el ciclo.
                _free_from_appointment(
                    repo,
                    existing,
                    source="reprogramada",
                    now=now,
                    default_duration_minutes=default_duration_minutes,
                )
                repo.skip_pending_reminders(appointment_id)
                status = _status_for(event, repo).value
            elif phone_changed:
                if event.phone is None:
                    status = AppointmentStatus.NO_PHONE.value
                    repo.skip_pending_reminders(appointment_id)
                elif existing["phone"] is None:
                    # Apareció un teléfono válido (RF-2, RF-18).
                    status = _status_for(event, repo).value

            should_schedule = time_changed or (
                phone_changed and existing["phone"] is None
            )
            repo.update_appointment_details(
                appointment_id,
                patient_name=event.patient_name,
                phone=event.phone,
                starts_at=event.starts_at,
                ends_at=ends_at,
                status=status,
                updated_at=now,
            )

        if event.phone is not None and should_schedule:
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
            _free_from_appointment(
                repo,
                appointment,
                source="cancelada",
                now=now,
                default_duration_minutes=default_duration_minutes,
            )
            repo.delete_appointment(appointment["id"])

    _close_occupied_slots(repo, now)


def _status_for(event, repo: Repository) -> AppointmentStatus:
    """Estado inicial de una cita según teléfono y consentimiento (RF-2, RF-8)."""
    if event.phone is None:
        return AppointmentStatus.NO_PHONE
    patient = repo.get_patient(event.phone)
    if patient is None or not patient["has_consent"]:
        return AppointmentStatus.NO_CONSENT
    return AppointmentStatus.PENDING


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

def _free_from_appointment(
    repo: Repository,
    appointment: dict,
    *,
    source: str,
    now: datetime,
    default_duration_minutes: int,
) -> None:
    """Crea un espacio liberado a partir de una cita que sale del calendario."""
    starts_at = datetime.fromisoformat(appointment["starts_at"])
    stored_end = appointment.get("ends_at")
    if stored_end:
        ends_at = datetime.fromisoformat(stored_end)
        duration_estimated = False
    else:
        ends_at = starts_at + timedelta(minutes=default_duration_minutes)
        duration_estimated = True
    repo.create_freed_slot(
        event_id=appointment["event_id"],
        starts_at=starts_at,
        ends_at=ends_at,
        duration_estimated=duration_estimated,
        source=source,
        created_at=now,
    )


def _close_occupied_slots(repo: Repository, now: datetime) -> None:
    """Cierra espacios que ya fueron ocupados por otra cita."""
    for slot in repo.list_open_freed_slots():
        if slot["status"] == "reservado_pendiente":
            continue
        if repo.has_appointment_at(datetime.fromisoformat(slot["starts_at"])):
            active = repo.get_active_offer_for_slot(slot["id"])
            if active is not None:
                repo.update_slot_offer(
                    active["id"], status="cancelada", responded_at=now
                )
            repo.set_freed_slot_status(slot["id"], "ocupado")
