"""Calendario simulado para el modo demo (constitución 13).

En modo demo este calendario representa Google Calendar, la fuente de verdad
de las citas. Además de leerse, permite crear, mover y cancelar citas
ficticias para demostrar la sincronización (RF-3, CA-7).
"""

from __future__ import annotations

from datetime import datetime

from app.ports.calendar import CalendarEvent


class FakeCalendar:
    """Calendario con datos ficticios, sin credenciales."""

    def __init__(self, events: list[CalendarEvent] | None = None) -> None:
        self.events: list[CalendarEvent] = list(events) if events else []
        self._seq = 1000

    def list_events(
        self, sync_token: str | None = None
    ) -> tuple[list[CalendarEvent], str | None]:
        """Devuelve una copia de los eventos actuales (sin token incremental)."""
        return list(self.events), None

    def create_event(
        self, patient_name: str, starts_at: datetime, phone: str | None
    ) -> CalendarEvent:
        """Agrega una cita ficticia (simula crearla en Google Calendar)."""
        self._seq += 1
        event = CalendarEvent(
            event_id=f"evt-{self._seq}",
            patient_name=patient_name,
            starts_at=starts_at,
            phone=phone,
        )
        self.events.append(event)
        return event

    def update_event(
        self,
        event_id: str,
        *,
        patient_name: str,
        phone: str | None,
        starts_at: datetime,
    ) -> bool:
        """Edita nombre, teléfono y fecha de una cita ficticia (RF-18)."""
        for i, event in enumerate(self.events):
            if event.event_id == event_id:
                self.events[i] = CalendarEvent(
                    event_id=event.event_id,
                    patient_name=patient_name,
                    starts_at=starts_at,
                    phone=phone,
                )
                return True
        return False

    def move_event(self, event_id: str, starts_at: datetime) -> bool:
        """Mueve una cita a otra fecha/hora (simula editarla en el calendario)."""
        for event in list(self.events):
            if event.event_id == event_id:
                return self.update_event(
                    event_id,
                    patient_name=event.patient_name,
                    phone=event.phone,
                    starts_at=starts_at,
                )
        return False

    def cancel_event(self, event_id: str) -> bool:
        """Elimina una cita (simula cancelarla en el calendario)."""
        before = len(self.events)
        self.events = [e for e in self.events if e.event_id != event_id]
        return len(self.events) < before
