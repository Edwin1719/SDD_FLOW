"""Esquema SQLite y creación de la base de datos (T3)."""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 2

_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        patient_name TEXT NOT NULL,
        phone TEXT,
        starts_at TEXT NOT NULL,
        ends_at TEXT,
        status TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS patients (
        phone TEXT PRIMARY KEY,
        has_consent INTEGER NOT NULL DEFAULT 0,
        opted_out INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL REFERENCES appointments(id),
        kind TEXT NOT NULL,
        starts_at_snapshot TEXT NOT NULL,
        scheduled_for TEXT NOT NULL,
        sent_at TEXT,
        state TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        UNIQUE (appointment_id, kind, starts_at_snapshot)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL REFERENCES appointments(id),
        action TEXT NOT NULL,
        received_at TEXT NOT NULL,
        applied INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS waitlist_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        reason TEXT NOT NULL,
        preferred_days TEXT NOT NULL DEFAULT '',
        preferred_time_start TEXT,
        preferred_time_end TEXT,
        source TEXT NOT NULL DEFAULT 'asistente',
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'activa',
        last_offered_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS freed_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        starts_at TEXT NOT NULL,
        ends_at TEXT NOT NULL,
        duration_estimated INTEGER NOT NULL DEFAULT 0,
        source TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'libre',
        recovered_at TEXT,
        UNIQUE (event_id, starts_at, ends_at)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS slot_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        freed_slot_id INTEGER NOT NULL REFERENCES freed_slots(id),
        waitlist_entry_id INTEGER NOT NULL REFERENCES waitlist_entries(id),
        sent_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        responded_at TEXT,
        response TEXT,
        status TEXT NOT NULL DEFAULT 'enviada'
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_offer_active_slot"
    " ON slot_offers(freed_slot_id) WHERE status = 'enviada'",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_offer_active_entry"
    " ON slot_offers(waitlist_entry_id) WHERE status = 'enviada'",
    "CREATE INDEX IF NOT EXISTS idx_freed_slots_status ON freed_slots(status)",
]


def init_schema(connection: sqlite3.Connection) -> None:
    """Crea las tablas si no existen, migra v1 a v2 y fija la versión."""
    for statement in _DDL:
        connection.execute(statement)

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(appointments)")
    }
    if "ends_at" not in columns:
        connection.execute("ALTER TABLE appointments ADD COLUMN ends_at TEXT")

    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    connection.commit()
