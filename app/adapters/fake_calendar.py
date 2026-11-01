"""Calendario simulado para el modo demo (constitución 13)."""

from __future__ import annotations

from app.ports.calendar import CalendarEvent


class FakeCalendar:
    """Calendario con datos ficticios, sin credenciales."""

    def __init__(self, events: list[CalendarEvent] | None = None) -> None:
        self.events: list[CalendarEvent] = list(events) if events else []

    def list_events(
        self, sync_token: str | None = None
    ) -> tuple[list[CalendarEvent], str | None]:
        """Devuelve una copia de los eventos actuales (sin token incremental)."""
        return list(self.events), None
