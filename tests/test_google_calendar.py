"""Tests del adaptador real de Google Calendar (T14).

Usan respuestas simuladas; ninguna llamada real a Google.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from app.adapters.google_calendar import GoogleCalendar


def _calendar(service) -> GoogleCalendar:
    return GoogleCalendar(service, "primary")


def _event(
    event_id, date_time, summary="Paciente", description="Tel: +57 300 123 4567"
):
    return {
        "id": event_id,
        "summary": summary,
        "start": {"dateTime": date_time},
        "description": description,
    }


def test_parses_events_and_extracts_phone():
    service = MagicMock()
    service.events().list().execute.return_value = {
        "items": [_event("evt-1", "2026-11-04T12:00:00-05:00")],
        "nextSyncToken": "token-1",
    }

    events, token = _calendar(service).list_events()

    assert token == "token-1"
    assert len(events) == 1
    assert events[0].event_id == "evt-1"
    assert events[0].patient_name == "Paciente"
    assert events[0].phone == "+573001234567"
    assert events[0].starts_at.tzinfo is not None  # con zona horaria


def test_skips_cancelled_events():
    service = MagicMock()
    service.events().list().execute.return_value = {
        "items": [
            {"id": "evt-1", "status": "cancelled"},
            _event("evt-2", "2026-11-04T12:00:00Z"),
        ],
        "nextSyncToken": "token-2",
    }

    events, _token = _calendar(service).list_events()
    assert [e.event_id for e in events] == ["evt-2"]


def test_passes_sync_token():
    service = MagicMock()
    service.events().list().execute.return_value = {"items": [], "nextSyncToken": "t"}

    _calendar(service).list_events("prev-token")

    kwargs = service.events().list.call_args.kwargs
    assert kwargs["syncToken"] == "prev-token"


def test_410_retries_without_token():
    service = MagicMock()
    service.events().list.return_value.execute.side_effect = [
        HttpError(SimpleNamespace(status=410, reason="Gone"), b"sync token expired"),
        {"items": [], "nextSyncToken": "fresh"},
    ]

    events, token = _calendar(service).list_events("stale-token")

    assert token == "fresh"
    calls = service.events().list.call_args_list
    assert calls[0].kwargs["syncToken"] == "stale-token"
    assert calls[1].kwargs["syncToken"] is None
