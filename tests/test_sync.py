"""Tests de sincronización con el calendario (T6).

Criterios de T6: cita nueva, movida, cancelada, sin teléfono, teléfono mal
escrito y fallo de lectura sin perder datos (RF-1 a RF-3).
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.fake_calendar import FakeCalendar
from app.db.repository import connect
from app.domain.phone import extract_phone
from app.ports.calendar import CalendarEvent
from app.services.sync import sync_calendar

UTC = timezone.utc
NOW = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
T1 = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
T2 = datetime(2026, 11, 11, 14, 0, tzinfo=UTC)


def _event(
    event_id: str, starts_at: datetime, phone: str | None = "+573001234567"
) -> CalendarEvent:
    return CalendarEvent(
        event_id=event_id, patient_name="Paciente", starts_at=starts_at, phone=phone
    )


def test_new_appointment_created(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    calendar = FakeCalendar([_event("evt-1", T1)])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    appointment = repo.get_appointment("evt-1")
    assert appointment is not None
    assert appointment["status"] == "pending"
    assert appointment["starts_at"] == T1.isoformat()

    reminders = repo.list_reminders(appointment["id"])
    assert {r["kind"] for r in reminders} == {"R1", "R2"}
    repo.close()


def test_moved_appointment_resets_and_reschedules(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    calendar = FakeCalendar([_event("evt-1", T1)])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)
    appointment = repo.get_appointment("evt-1")
    assert len(repo.list_reminders(appointment["id"])) == 2

    calendar.events = [_event("evt-1", T2)]
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    appointment = repo.get_appointment("evt-1")
    assert appointment["starts_at"] == T2.isoformat()
    assert appointment["status"] == "pending"

    reminders = repo.list_reminders(appointment["id"])
    assert len(reminders) == 4
    assert sum(1 for r in reminders if r["state"] == "skipped") == 2
    assert sum(1 for r in reminders if r["state"] == "pending") == 2
    repo.close()


def test_cancelled_appointment_removed(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    calendar = FakeCalendar([_event("evt-1", T1), _event("evt-2", T1)])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)
    assert repo.get_appointment("evt-1") is not None
    assert repo.get_appointment("evt-2") is not None

    calendar.events = [_event("evt-2", T1)]
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    assert repo.get_appointment("evt-1") is None
    assert repo.get_appointment("evt-2") is not None
    repo.close()


def test_appointment_without_phone_gets_no_phone(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    calendar = FakeCalendar([_event("evt-1", T1, phone=None)])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "no_phone"
    assert repo.list_reminders(appointment["id"]) == []
    repo.close()


def test_malformed_phone_gets_no_phone(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    event = CalendarEvent(
        event_id="evt-1",
        patient_name="Paciente",
        starts_at=T1,
        phone=extract_phone("Tel: 300123"),  # sin "+" → None
    )
    calendar = FakeCalendar([event])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    appointment = repo.get_appointment("evt-1")
    assert appointment["status"] == "no_phone"
    repo.close()


class _FailingCalendar:
    def list_events(self, sync_token=None):
        raise RuntimeError("calendar read failed")


def test_read_failure_preserves_local_data(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.create_appointment(
        event_id="evt-1",
        patient_name="Paciente",
        phone="+573001234567",
        starts_at=T1,
        status="pending",
        updated_at=NOW,
    )

    with pytest.raises(RuntimeError):
        sync_calendar(_FailingCalendar(), repo, now=NOW, clinic_tz=UTC)

    appointment = repo.get_appointment("evt-1")
    assert appointment is not None
    assert appointment["status"] == "pending"
    repo.close()

def test_phone_added_without_moving_updates_and_schedules(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    calendar = FakeCalendar([_event("evt-1", T1, phone=None)])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    assert repo.get_appointment("evt-1")["status"] == "no_phone"

    repo.upsert_patient("+573009998877", has_consent=True)
    calendar.events = [_event("evt-1", T1, phone="+573009998877")]
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    appointment = repo.get_appointment("evt-1")
    assert appointment["phone"] == "+573009998877"
    assert appointment["status"] == "pending"
    assert {r["kind"] for r in repo.list_reminders(appointment["id"])} == {"R1", "R2"}
    repo.close()


def test_name_change_without_moving_updates_local(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    calendar = FakeCalendar([_event("evt-1", T1)])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    calendar.events = [
        CalendarEvent(
            event_id="evt-1",
            patient_name="Nombre Corregido",
            starts_at=T1,
            phone="+573001234567",
        )
    ]
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    assert repo.get_appointment("evt-1")["patient_name"] == "Nombre Corregido"
    repo.close()

def test_cancel_creates_freed_slot(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    event = CalendarEvent(
        event_id="evt-1",
        patient_name="Paciente",
        starts_at=T1,
        phone="+573001234567",
        ends_at=T1 + timedelta(minutes=30),
    )
    calendar = FakeCalendar([event])
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    calendar.events = []
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    slots = repo.list_freed_slots()
    assert len(slots) == 1
    assert slots[0]["source"] == "cancelada"
    assert slots[0]["starts_at"] == T1.isoformat()
    assert slots[0]["ends_at"] == (T1 + timedelta(minutes=30)).isoformat()
    assert slots[0]["duration_estimated"] == 0
    repo.close()


def test_move_creates_freed_slot_with_old_time(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    calendar = FakeCalendar(
        [
            CalendarEvent(
                event_id="evt-1",
                patient_name="Paciente",
                starts_at=T1,
                phone="+573001234567",
                ends_at=T1 + timedelta(minutes=30),
            )
        ]
    )
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    calendar.events = [
        CalendarEvent(
            event_id="evt-1",
            patient_name="Paciente",
            starts_at=T2,
            phone="+573001234567",
            ends_at=T2 + timedelta(minutes=30),
        )
    ]
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    slots = repo.list_freed_slots()
    assert len(slots) == 1
    assert slots[0]["source"] == "reprogramada"
    assert slots[0]["starts_at"] == T1.isoformat()
    repo.close()


def test_missing_end_uses_estimated_duration(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    calendar = FakeCalendar(
        [
            CalendarEvent(
                event_id="evt-1",
                patient_name="Paciente",
                starts_at=T1,
                phone="+573001234567",
            )
        ]
    )
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    calendar.events = []
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    slot = repo.list_freed_slots()[0]
    assert slot["ends_at"] == (T1 + timedelta(minutes=30)).isoformat()
    assert slot["duration_estimated"] == 1
    repo.close()


def test_new_appointment_occupies_freed_slot(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    repo.upsert_patient("+573001234567", has_consent=True)
    calendar = FakeCalendar(
        [
            CalendarEvent(
                event_id="evt-1",
                patient_name="Paciente",
                starts_at=T1,
                phone="+573001234567",
                ends_at=T1 + timedelta(minutes=30),
            )
        ]
    )
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)
    calendar.events = []
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)
    slot = repo.list_freed_slots()[0]

    calendar.events = [
        CalendarEvent(
            event_id="evt-2",
            patient_name="Otro",
            starts_at=T1,
            phone="+573009999999",
            ends_at=T1 + timedelta(minutes=30),
        )
    ]
    sync_calendar(calendar, repo, now=NOW, clinic_tz=UTC)

    assert repo.get_freed_slot(slot["id"])["status"] == "ocupado"
    repo.close()
