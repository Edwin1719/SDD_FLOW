"""Tests de las transiciones de estado del dominio (T4).

Criterios de T4: confirmar, reprogramar, cancelar, «última respuesta manda»
y Sin confirmar (RF-11 a RF-15).
"""

from datetime import datetime, timedelta, timezone

from app.domain.models import Appointment, AppointmentStatus, ReplyAction
from app.domain.rules import apply_reply, mark_unconfirmed

_START = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def _appointment(status: AppointmentStatus) -> Appointment:
    return Appointment(
        event_id="evt-1",
        patient_name="Ana",
        phone="+5712345678",
        starts_at=_START,
        status=status,
    )


def _received_before() -> datetime:
    return _START - timedelta(days=2)


def test_confirm_marks_confirmed():
    appointment = _appointment(AppointmentStatus.REMINDER_SENT)
    result = apply_reply(appointment, ReplyAction.CONFIRM, _received_before())
    assert result.status == AppointmentStatus.CONFIRMED


def test_reschedule_marks_reschedule_requested():
    appointment = _appointment(AppointmentStatus.REMINDER_SENT)
    result = apply_reply(appointment, ReplyAction.RESCHEDULE, _received_before())
    assert result.status == AppointmentStatus.RESCHEDULE_REQUESTED


def test_cancel_marks_cancelled_by_patient():
    appointment = _appointment(AppointmentStatus.REMINDER_SENT)
    result = apply_reply(appointment, ReplyAction.CANCEL, _received_before())
    assert result.status == AppointmentStatus.CANCELLED_BY_PATIENT


def test_last_reply_wins():
    appointment = _appointment(AppointmentStatus.REMINDER_SENT)
    appointment = apply_reply(appointment, ReplyAction.CONFIRM, _received_before())
    appointment = apply_reply(appointment, ReplyAction.CANCEL, _received_before())
    assert appointment.status == AppointmentStatus.CANCELLED_BY_PATIENT


def test_late_reply_ignored():
    appointment = _appointment(AppointmentStatus.REMINDER_SENT)
    late = _START + timedelta(hours=1)
    result = apply_reply(appointment, ReplyAction.CONFIRM, late)
    assert result.status == AppointmentStatus.REMINDER_SENT


def test_unconfirmed_marks_not_confirmed():
    appointment = _appointment(AppointmentStatus.REMINDER_SENT)
    result = mark_unconfirmed(appointment)
    assert result.status == AppointmentStatus.UNCONFIRMED


def test_confirmed_stays_confirmed():
    appointment = _appointment(AppointmentStatus.CONFIRMED)
    result = mark_unconfirmed(appointment)
    assert result.status == AppointmentStatus.CONFIRMED


def test_cancelled_stays_cancelled():
    appointment = _appointment(AppointmentStatus.CANCELLED_BY_PATIENT)
    result = mark_unconfirmed(appointment)
    assert result.status == AppointmentStatus.CANCELLED_BY_PATIENT
