"""Tests del esquema y repositorio SQLite (T3).

Criterios de T3: creación al arrancar (incluida la carpeta `data/`),
reapertura sin perder datos y rechazo de recordatorio duplicado (RF-10).
"""

import sqlite3
from datetime import datetime, timezone

import pytest

from app.db.repository import connect


def _utc(hour: int) -> datetime:
    return datetime(2026, 10, 31, hour, 0, tzinfo=timezone.utc)


def test_connect_creates_folder_and_schema(tmp_path):
    db_path = tmp_path / "data" / "recordatorios.db"
    repo = connect(db_path)
    repo.close()

    assert db_path.parent.is_dir()  # carpeta data/ creada
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
            " AND name NOT LIKE 'sqlite_%'"
        )
    }
    assert tables == {"appointments", "patients", "reminders", "replies", "sync_state"}
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
    conn.close()


def test_reopen_preserves_data(tmp_path):
    db_path = tmp_path / "data" / "recordatorios.db"
    repo = connect(db_path)
    repo.create_appointment(
        event_id="evt-1",
        patient_name="Ana",
        phone="+5712345678",
        starts_at=_utc(10),
        status="pending",
        updated_at=_utc(8),
    )
    repo.close()

    repo = connect(db_path)
    appointment = repo.get_appointment("evt-1")
    assert appointment is not None
    assert appointment["patient_name"] == "Ana"
    assert appointment["phone"] == "+5712345678"
    repo.close()


def test_duplicate_reminder_rejected(tmp_path):
    db_path = tmp_path / "data" / "recordatorios.db"
    repo = connect(db_path)
    appointment_id = repo.create_appointment(
        event_id="evt-2",
        patient_name="Luis",
        phone="+573001112223",
        starts_at=_utc(12),
        status="pending",
        updated_at=_utc(8),
    )
    snapshot = _utc(10)
    repo.create_reminder(
        appointment_id=appointment_id,
        kind="R1",
        starts_at_snapshot=snapshot,
        scheduled_for=_utc(10),
    )

    with pytest.raises(sqlite3.IntegrityError):
        repo.create_reminder(
            appointment_id=appointment_id,
            kind="R1",
            starts_at_snapshot=snapshot,
            scheduled_for=_utc(10),
        )

    assert len(repo.list_reminders(appointment_id)) == 1
    repo.close()
