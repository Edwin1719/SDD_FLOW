"""Puerto del calendario: solo lectura de la agenda (constitución 3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class CalendarEvent:
    """Evento de la agenda tal como lo entrega el calendario (RF-1)."""

    event_id: str
    patient_name: str
    starts_at: datetime  # en UTC
    phone: str | None  # None si no hay teléfono con el formato esperado (RF-2)


class CalendarPort(Protocol):
    """Fuente de la agenda (Google Calendar en real, FakeCalendar en demo)."""

    def list_events(
        self, sync_token: str | None = None
    ) -> tuple[list[CalendarEvent], str | None]:
        """Devuelve los eventos y el nuevo token de sincronización incremental.

        Con `sync_token` se pide solo lo que cambió desde la última lectura;
        sin token, la agenda completa.
        """
        ...
