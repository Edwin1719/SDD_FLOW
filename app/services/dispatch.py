"""Envío de recordatorios pendientes (T7).

Envía los recordatorios cuyo momento ya llegó, respetando el consentimiento,
con reintentos limitados e idempotencia (RF-4, RF-5, RF-8, RF-10, RF-16).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.db.repository import Repository
from app.ports.messaging import MessagingPort

# Estados de cita que no deben recibir el recordatorio 2 (RF-5).
_NO_SEND_STATUSES = {"cancelled_by_patient", "reschedule_requested"}

_DEFAULT_RETRY_DELAYS = (
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=15),
)


def dispatch_due_reminders(
    repo: Repository,
    messaging: MessagingPort,
    *,
    now: datetime,
    max_attempts: int = 3,
    retry_delays: tuple[timedelta, ...] = _DEFAULT_RETRY_DELAYS,
) -> None:
    """Envía los recordatorios pendientes cuyo momento ya llegó."""
    for reminder in repo.list_due_reminders(now):
        _dispatch_reminder(repo, messaging, reminder, now, max_attempts, retry_delays)


def _dispatch_reminder(
    repo: Repository,
    messaging: MessagingPort,
    reminder: dict,
    now: datetime,
    max_attempts: int,
    retry_delays: tuple[timedelta, ...],
) -> None:
    appointment = repo.get_appointment_by_id(reminder["appointment_id"])
    if appointment is None:
        repo.mark_reminder_skipped(reminder["id"])
        return

    # RF-5: no enviar a canceladas ni reprogramadas (evaluado al enviar).
    if appointment["status"] in _NO_SEND_STATUSES:
        repo.mark_reminder_skipped(reminder["id"])
        return

    # RF-8: sin consentimiento no se envía.
    phone = appointment["phone"]
    patient = repo.get_patient(phone) if phone else None
    if patient is None or not patient["has_consent"]:
        repo.mark_reminder_skipped(reminder["id"])
        repo.update_appointment_status(appointment["id"], "no_consent", now)
        return
    # RF-9: baja — no se envían más mensajes a ese teléfono.
    if patient["opted_out"]:
        repo.mark_reminder_skipped(reminder["id"])
        return

    # RF-16: enviar con reintentos limitados e idempotencia (RF-10).
    try:
        messaging.send(phone, f"Recordatorio {reminder['kind']}")
    except Exception as exc:  # cualquier fallo de envío dispara el reintento
        attempts = reminder["attempts"] + 1
        if attempts >= max_attempts:
            repo.mark_reminder_failed(
                reminder["id"], attempts=attempts, last_error=str(exc)
            )
            repo.update_appointment_status(appointment["id"], "send_error", now)
        else:
            repo.reschedule_reminder(
                reminder["id"],
                scheduled_for=now + retry_delays[attempts - 1],
                attempts=attempts,
                last_error=str(exc),
            )
    else:
        repo.mark_reminder_sent(reminder["id"], now)
        if appointment["status"] == "pending":
            repo.update_appointment_status(appointment["id"], "reminder_sent", now)
