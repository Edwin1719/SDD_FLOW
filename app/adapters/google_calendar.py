"""Adaptador real de Google Calendar (solo lectura)."""

from __future__ import annotations

from datetime import datetime, timezone

from googleapiclient.errors import HttpError

from app.domain.phone import extract_phone
from app.ports.calendar import CalendarEvent


class GoogleCalendar:
    """Lee citas de Google Calendar con sincronización incremental (syncToken)."""

    def __init__(self, service, calendar_id: str) -> None:
        self._service = service
        self._calendar_id = calendar_id

    def list_events(
        self, sync_token: str | None = None
    ) -> tuple[list[CalendarEvent], str | None]:
        """Devuelve los eventos activos y el nuevo token de sincronización.

        Ante un 410 (token expirado) repite la sincronización completa sin token.
        """
        try:
            page = self._fetch(sync_token)
        except HttpError as exc:
            if exc.resp.status == 410:
                page = self._fetch(None)
            else:
                raise

        events: list[CalendarEvent] = []
        for item in page.get("items", []):
            # Evento eliminado: se detecta por ausencia en la sincronización completa.
            if item.get("status") == "cancelled":
                continue
            event = self._parse(item)
            if event is not None:
                events.append(event)
        return events, page.get("nextSyncToken")

    def _fetch(self, sync_token: str | None):
        request = self._service.events().list(
            calendarId=self._calendar_id,
            syncToken=sync_token,
            singleEvents=True,
        )
        return request.execute()

    def _parse(self, item: dict) -> CalendarEvent | None:
        start = item.get("start", {})
        date_time = start.get("dateTime")
        if date_time is None:
            return None  # evento de día completo sin hora: se omite
        starts_at = datetime.fromisoformat(date_time).astimezone(timezone.utc)
        end = item.get("end", {})
        end_time = end.get("dateTime")
        ends_at = (
            datetime.fromisoformat(end_time).astimezone(timezone.utc)
            if end_time
            else None
        )
        return CalendarEvent(
            event_id=item["id"],
            patient_name=item.get("summary", ""),
            starts_at=starts_at,
            phone=extract_phone(item.get("description", "")),
            ends_at=ends_at,
        )
