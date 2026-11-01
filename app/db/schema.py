"""Esquema SQLite y creación de la base de datos (T3)."""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        patient_name TEXT NOT NULL,
        phone TEXT,
        starts_at TEXT NOT NULL,
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
]


def init_schema(connection: sqlite3.Connection) -> None:
    """Crea las tablas si no existen y fija la versión del esquema."""
    for statement in _DDL:
        connection.execute(statement)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    connection.commit()
