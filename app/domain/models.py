"""Modelos del dominio: cita, estados y acciones (sin E/S)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AppointmentStatus(StrEnum):
    """Estados de una cita (spec 4.2)."""

    PENDING = "pending"
    REMINDER_SENT = "reminder_sent"
    CONFIRMED = "confirmed"
    RESCHEDULE_REQUESTED = "reschedule_requested"
    CANCELLED_BY_PATIENT = "cancelled_by_patient"
    UNCONFIRMED = "unconfirmed"
    SEND_ERROR = "send_error"
    NO_CONSENT = "no_consent"
    NO_PHONE = "no_phone"


class ReplyAction(StrEnum):
    """Acciones de respuesta del paciente (botones y baja)."""

    CONFIRM = "confirm"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    OPTOUT = "optout"


@dataclass(frozen=True)
class Appointment:
    """Cita tal como la maneja el dominio (identidad y estado)."""

    event_id: str
    patient_name: str
    phone: str | None
    starts_at: datetime
    status: AppointmentStatus
