"""Cálculo de envío de recordatorios (T5).

Lógica pura (sin E/S): calcula qué recordatorios programar para una cita,
aplicando la ventana de envío en la zona horaria del consultorio.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone, tzinfo
from enum import StrEnum


class ReminderKind(StrEnum):
    """Tipos de recordatorio (plan.md, tabla reminders)."""

    R1 = "R1"
    R2 = "R2"
    IMMEDIATE = "IMMEDIATE"


@dataclass(frozen=True)
class ScheduledReminder:
    """Recordatorio a programar: tipo y momento de envío (UTC)."""

    kind: ReminderKind
    scheduled_for: datetime


def _snap_to_window(
    t: datetime, tz: tzinfo, window_start: time, window_end: time
) -> datetime:
    """Devuelve el primer instante en ventana mayor o igual a `t`, en UTC.

    Si `t` cae fuera de [window_start, window_end) en la zona `tz`, se mueve
    al inicio de la siguiente ventana (RF-7).
    """
    local = t.astimezone(tz)
    if window_start <= local.time() < window_end:
        return t
    if local.time() < window_start:
        target_day = local.date()
    else:  # local.time() >= window_end
        target_day = local.date() + timedelta(days=1)
    target = datetime.combine(target_day, window_start, tzinfo=tz)
    return target.astimezone(timezone.utc)


def compute_reminders(
    *,
    starts_at: datetime,
    now: datetime,
    clinic_tz: tzinfo,
    window_start: time = time(8, 0),
    window_end: time = time(20, 0),
) -> list[ScheduledReminder]:
    """Calcula los recordatorios a programar para una cita (RF-4 a RF-7).

    - R1 a 48 h antes y R2 a 24 h antes (RF-4, RF-5).
    - Si faltan menos de 48 h se omite R1; si faltan menos de 24 h se envía
      un único recordatorio inmediato (RF-6).
    - Los envíos solo dentro de la ventana en hora del consultorio; lo que
      caiga fuera pasa al inicio de la siguiente ventana (RF-7).
    """
    r1 = _snap_to_window(
        starts_at - timedelta(hours=48), clinic_tz, window_start, window_end
    )
    r2 = _snap_to_window(
        starts_at - timedelta(hours=24), clinic_tz, window_start, window_end
    )

    reminders: list[ScheduledReminder] = []

    if r1 <= starts_at and r1 >= now:
        reminders.append(ScheduledReminder(ReminderKind.R1, r1))

    if r2 <= starts_at and r2 >= now:
        reminders.append(ScheduledReminder(ReminderKind.R2, r2))
    elif now < starts_at:
        immediate = _snap_to_window(now, clinic_tz, window_start, window_end)
        if immediate <= starts_at:
            reminders.append(ScheduledReminder(ReminderKind.IMMEDIATE, immediate))

    return reminders
