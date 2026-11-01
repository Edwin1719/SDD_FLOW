"""Tests del cálculo de envío de recordatorios (T5).

Criterios de T5: 48 h, 24 h, menos de 48 h, menos de 24 h, hora fuera de
ventana y cambio de horario (RF-4 a RF-7).
"""

from datetime import datetime, timedelta, timezone
from app.domain.scheduling import ReminderKind, ScheduledReminder, compute_reminders

UTC = timezone.utc
# Zona horaria del consultorio: UTC-5.
CLINIC_TZ = timezone(timedelta(hours=-5))


def _dt(day: int, hour: int) -> datetime:
    return datetime(2026, 10, day, hour, 0, tzinfo=UTC)


def test_schedules_r1_and_r2_when_48h_ahead():
    starts_at = _dt(31, 19)  # 14:00 en el consultorio (UTC-5)
    now = _dt(28, 12)
    result = compute_reminders(starts_at=starts_at, now=now, clinic_tz=CLINIC_TZ)
    assert result == [
        ScheduledReminder(ReminderKind.R1, _dt(29, 19)),
        ScheduledReminder(ReminderKind.R2, _dt(30, 19)),
    ]


def test_skips_r1_when_less_than_48h():
    starts_at = _dt(31, 19)
    now = _dt(30, 10)  # 33 h antes
    result = compute_reminders(starts_at=starts_at, now=now, clinic_tz=CLINIC_TZ)
    assert result == [ScheduledReminder(ReminderKind.R2, _dt(30, 19))]


def test_sends_immediate_when_less_than_24h():
    starts_at = _dt(31, 19)
    now = _dt(31, 15)  # 10:00 en el consultorio, dentro de ventana
    result = compute_reminders(starts_at=starts_at, now=now, clinic_tz=CLINIC_TZ)
    assert result == [ScheduledReminder(ReminderKind.IMMEDIATE, _dt(31, 15))]


def test_moves_out_of_window_to_next_start():
    starts_at = _dt(31, 11)  # 06:00 en el consultorio, fuera de ventana
    now = _dt(28, 12)
    result = compute_reminders(starts_at=starts_at, now=now, clinic_tz=CLINIC_TZ)
    # 06:00 → 08:00 en el consultorio = 13:00 UTC
    assert result == [
        ScheduledReminder(ReminderKind.R1, _dt(29, 13)),
        ScheduledReminder(ReminderKind.R2, _dt(30, 13)),
    ]


def test_window_respects_clinic_timezone():
    starts_at = _dt(31, 22)  # 17:00 en el consultorio (en ventana; 22:00 UTC)
    now = _dt(28, 12)
    result = compute_reminders(starts_at=starts_at, now=now, clinic_tz=CLINIC_TZ)
    # 17:00 local está en ventana: no se mueve aunque en UTC sea 22:00
    assert result == [
        ScheduledReminder(ReminderKind.R1, _dt(29, 22)),
        ScheduledReminder(ReminderKind.R2, _dt(30, 22)),
    ]


def test_r2_scheduled_exactly_at_24h():
    starts_at = _dt(31, 19)
    now = _dt(30, 19)  # exactamente 24 h antes
    result = compute_reminders(starts_at=starts_at, now=now, clinic_tz=CLINIC_TZ)
    assert result == [ScheduledReminder(ReminderKind.R2, _dt(30, 19))]
