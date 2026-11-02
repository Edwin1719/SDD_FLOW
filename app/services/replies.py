"""Aplicación de respuestas del paciente (T8).

Aplica las respuestas de botón (confirmar/reprogramar/cancelar) y las bajas
(«BAJA»), ignorando respuestas tardías o de fechas ya cambiadas
(RF-9, RF-11 a RF-14).
"""

from __future__ import annotations

from datetime import datetime

from app.db.repository import Repository
from app.domain.models import Appointment, AppointmentStatus, ReplyAction
from app.domain.rules import apply_reply as _domain_apply_reply
from app.ports.messaging import MessagingPort
from app.texts_es import AUTO_REPLY


def apply_button_reply(
    repo: Repository,
    messaging: MessagingPort,
    *,
    appointment_id: int,
    action: ReplyAction,
    original_starts_at: datetime,
    received_at: datetime,
) -> bool:
    """Aplica una respuesta de botón; devuelve True si cambió el estado.

    Se ignora (applied=False) si la respuesta es posterior a la cita o si la
    fecha original ya no coincide con la fecha actual de la cita (RF-14).
    """
    row = repo.get_appointment_by_id(appointment_id)
    if row is None:
        return False

    stored_starts = datetime.fromisoformat(row["starts_at"])
    if stored_starts != original_starts_at:
        repo.create_reply(
            appointment_id=appointment_id,
            action=action.value,
            received_at=received_at,
            applied=False,
        )
        return False

    appointment = Appointment(
        event_id=row["event_id"],
        patient_name=row["patient_name"],
        phone=row["phone"],
        starts_at=stored_starts,
        status=AppointmentStatus(row["status"]),
    )
    updated = _domain_apply_reply(appointment, action, received_at)
    applied = updated.status != appointment.status

    if applied:
        repo.update_appointment_status(
            appointment_id, updated.status.value, received_at
        )

    repo.create_reply(
        appointment_id=appointment_id,
        action=action.value,
        received_at=received_at,
        applied=applied,
    )

    if applied and appointment.phone:
        patient = repo.get_patient(appointment.phone)
        # RF-8 y RF-9: no responder a quien no dio consentimiento o pidió la baja.
        if patient is not None and patient["has_consent"] and not patient["opted_out"]:
            messaging.send(appointment.phone, AUTO_REPLY[action.value])

    return applied


def apply_optout(
    repo: Repository,
    *,
    appointment_id: int,
    received_at: datetime,
) -> None:
    """Aplica una baja: no se envían más mensajes a ese teléfono (RF-9)."""
    appointment = repo.get_appointment_by_id(appointment_id)
    if appointment is None or appointment["phone"] is None:
        return

    phone = appointment["phone"]
    repo.set_patient_opted_out(phone, True)
    repo.skip_pending_reminders_by_phone(phone)
    repo.create_reply(
        appointment_id=appointment_id,
        action=ReplyAction.OPTOUT.value,
        received_at=received_at,
        applied=True,
    )
