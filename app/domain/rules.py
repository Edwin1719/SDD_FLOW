"""Reglas de transición de estado del dominio (T4).

Lógica pura, sin E/S (constitución 7).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.domain.models import Appointment, AppointmentStatus, ReplyAction

_REPLY_TARGET: dict[ReplyAction, AppointmentStatus] = {
    ReplyAction.CONFIRM: AppointmentStatus.CONFIRMED,
    ReplyAction.RESCHEDULE: AppointmentStatus.RESCHEDULE_REQUESTED,
    ReplyAction.CANCEL: AppointmentStatus.CANCELLED_BY_PATIENT,
}


def apply_reply(
    appointment: Appointment, action: ReplyAction, received_at: datetime
) -> Appointment:
    """Aplica una respuesta del paciente a la cita.

    Una respuesta que llega después de la hora de la cita se ignora (RF-14).
    La última respuesta recibida antes de la cita define el estado (RF-14).
    """
    if received_at > appointment.starts_at:
        return appointment
    return replace(appointment, status=_REPLY_TARGET[action])


def mark_unconfirmed(appointment: Appointment) -> Appointment:
    """Marca Sin confirmar una cita tras el recordatorio 2 sin respuesta (RF-15).

    Solo una cita en «Recordatorio enviado» pasa a Sin confirmar: una cita ya
    Confirmada se mantiene Confirmada, y una cancelada o reprogramada no recibe
    el recordatorio 2, así que no llega a este estado.
    """
    if appointment.status != AppointmentStatus.REMINDER_SENT:
        return appointment
    return replace(appointment, status=AppointmentStatus.UNCONFIRMED)
