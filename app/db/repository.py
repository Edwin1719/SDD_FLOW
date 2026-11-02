"""Repositorio sobre SQLite: acceso a la base de datos (T3).

Las fechas se guardan en UTC como texto ISO 8601 (plan.md). El repositorio
acepta `datetime` y los serializa internamente.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.db.schema import init_schema


def _iso(value: datetime) -> str:
    return value.isoformat()


class Repository:
    """Acceso tipado a las tablas de SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.row_factory = sqlite3.Row

    def create_appointment(
        self,
        *,
        event_id: str,
        patient_name: str,
        phone: str | None,
        starts_at: datetime,
        status: str,
        updated_at: datetime,
    ) -> int:
        """Inserta una cita y devuelve su id."""
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO appointments
                    (event_id, patient_name, phone, starts_at, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    patient_name,
                    phone,
                    _iso(starts_at),
                    status,
                    _iso(updated_at),
                ),
            )
        return cursor.lastrowid

    def get_appointment(self, event_id: str) -> dict | None:
        """Devuelve la cita con ese event_id, o None si no existe."""
        row = self._conn.execute(
            "SELECT * FROM appointments WHERE event_id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def create_reminder(
        self,
        *,
        appointment_id: int,
        kind: str,
        starts_at_snapshot: datetime,
        scheduled_for: datetime,
        state: str = "pending",
    ) -> int:
        """Inserta un recordatorio y devuelve su id.

        Lanza `sqlite3.IntegrityError` si ya existe un recordatorio con la
        misma cita, tipo y fecha (clave única, RF-10).
        """
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO reminders
                    (appointment_id, kind, starts_at_snapshot, scheduled_for, state)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    appointment_id,
                    kind,
                    _iso(starts_at_snapshot),
                    _iso(scheduled_for),
                    state,
                ),
            )
        return cursor.lastrowid

    def list_reminders(self, appointment_id: int) -> list[dict]:
        """Devuelve los recordatorios de una cita, en orden de creación."""
        rows = self._conn.execute(
            "SELECT * FROM reminders WHERE appointment_id = ? ORDER BY id",
            (appointment_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_appointments(self) -> list[dict]:
        """Devuelve todas las citas, en orden de creación."""
        rows = self._conn.execute("SELECT * FROM appointments ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def update_appointment(
        self,
        appointment_id: int,
        *,
        starts_at: datetime,
        status: str,
        updated_at: datetime,
    ) -> None:
        """Actualiza fecha, estado y marca de tiempo de una cita."""
        with self._conn:
            self._conn.execute(
                "UPDATE appointments SET starts_at = ?, status = ?, updated_at = ?"
                " WHERE id = ?",
                (_iso(starts_at), status, _iso(updated_at), appointment_id),
            )

    def update_appointment_details(
        self,
        appointment_id: int,
        *,
        patient_name: str,
        phone: str | None,
        starts_at: datetime,
        status: str,
        updated_at: datetime,
    ) -> None:
        """Actualiza nombre, teléfono, fecha y estado de una cita (RF-18)."""
        with self._conn:
            self._conn.execute(
                "UPDATE appointments SET patient_name = ?, phone = ?,"
                " starts_at = ?, status = ?, updated_at = ? WHERE id = ?",
                (
                    patient_name,
                    phone,
                    _iso(starts_at),
                    status,
                    _iso(updated_at),
                    appointment_id,
                ),
            )

    def skip_pending_reminders(self, appointment_id: int) -> None:
        """Marca como skipped los recordatorios pendientes de una cita."""
        with self._conn:
            self._conn.execute(
                "UPDATE reminders SET state = 'skipped'"
                " WHERE appointment_id = ? AND state = 'pending'",
                (appointment_id,),
            )

    def delete_appointment(self, appointment_id: int) -> None:
        """Elimina una cita y sus recordatorios y respuestas."""
        with self._conn:
            self._conn.execute(
                "DELETE FROM reminders WHERE appointment_id = ?", (appointment_id,)
            )
            self._conn.execute(
                "DELETE FROM replies WHERE appointment_id = ?", (appointment_id,)
            )
            self._conn.execute(
                "DELETE FROM appointments WHERE id = ?", (appointment_id,)
            )

    def list_due_reminders(self, now: datetime) -> list[dict]:
        """Devuelve los recordatorios pendientes cuyo envío ya toca."""
        rows = self._conn.execute(
            "SELECT * FROM reminders"
            " WHERE state = 'pending' AND scheduled_for <= ?"
            " ORDER BY id",
            (_iso(now),),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_appointment_by_id(self, appointment_id: int) -> dict | None:
        """Devuelve la cita con ese id, o None si no existe."""
        row = self._conn.execute(
            "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def get_patient(self, phone: str) -> dict | None:
        """Devuelve el paciente con ese teléfono, o None si no existe."""
        row = self._conn.execute(
            "SELECT * FROM patients WHERE phone = ?", (phone,)
        ).fetchone()
        return dict(row) if row is not None else None

    def upsert_patient(
        self, phone: str, *, has_consent: bool, opted_out: bool = False
    ) -> None:
        """Crea o actualiza un paciente (consentimiento y baja)."""
        with self._conn:
            self._conn.execute(
                "INSERT INTO patients (phone, has_consent, opted_out)"
                " VALUES (?, ?, ?)"
                " ON CONFLICT(phone) DO UPDATE SET"
                " has_consent = excluded.has_consent,"
                " opted_out = excluded.opted_out",
                (phone, int(has_consent), int(opted_out)),
            )

    def mark_reminder_sent(self, reminder_id: int, sent_at: datetime) -> None:
        """Marca un recordatorio como enviado."""
        with self._conn:
            self._conn.execute(
                "UPDATE reminders SET state = 'sent', sent_at = ? WHERE id = ?",
                (_iso(sent_at), reminder_id),
            )

    def reschedule_reminder(
        self,
        reminder_id: int,
        *,
        scheduled_for: datetime,
        attempts: int,
        last_error: str,
    ) -> None:
        """Reprograma un recordatorio para un reintento posterior."""
        with self._conn:
            self._conn.execute(
                "UPDATE reminders SET scheduled_for = ?, attempts = ?, last_error = ?"
                " WHERE id = ?",
                (_iso(scheduled_for), attempts, last_error, reminder_id),
            )

    def mark_reminder_failed(
        self, reminder_id: int, *, attempts: int, last_error: str
    ) -> None:
        """Marca un recordatorio como fallido tras agotar reintentos."""
        with self._conn:
            self._conn.execute(
                "UPDATE reminders SET state = 'failed', attempts = ?, last_error = ?"
                " WHERE id = ?",
                (attempts, last_error, reminder_id),
            )

    def mark_reminder_skipped(self, reminder_id: int) -> None:
        """Marca un recordatorio como no enviado (skipped)."""
        with self._conn:
            self._conn.execute(
                "UPDATE reminders SET state = 'skipped' WHERE id = ?", (reminder_id,)
            )

    def update_appointment_status(
        self, appointment_id: int, status: str, updated_at: datetime
    ) -> None:
        """Actualiza el estado de una cita."""
        with self._conn:
            self._conn.execute(
                "UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?",
                (status, _iso(updated_at), appointment_id),
            )

    def create_reply(
        self,
        *,
        appointment_id: int,
        action: str,
        received_at: datetime,
        applied: bool,
    ) -> int:
        """Registra una respuesta del paciente y devuelve su id."""
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO replies (appointment_id, action, received_at, applied)"
                " VALUES (?, ?, ?, ?)",
                (appointment_id, action, _iso(received_at), int(applied)),
            )
        return cursor.lastrowid

    def list_replies(self, appointment_id: int) -> list[dict]:
        """Devuelve las respuestas de una cita, en orden de llegada."""
        rows = self._conn.execute(
            "SELECT * FROM replies WHERE appointment_id = ? ORDER BY id",
            (appointment_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def set_patient_opted_out(self, phone: str, opted_out: bool = True) -> None:
        """Marca o desmarca la baja de un paciente."""
        with self._conn:
            self._conn.execute(
                "UPDATE patients SET opted_out = ? WHERE phone = ?",
                (int(opted_out), phone),
            )

    def skip_pending_reminders_by_phone(self, phone: str) -> None:
        """Descarta los recordatorios pendientes de un teléfono."""
        with self._conn:
            self._conn.execute(
                "UPDATE reminders SET state = 'skipped'"
                " WHERE state = 'pending' AND appointment_id IN"
                " (SELECT id FROM appointments WHERE phone = ?)",
                (phone,),
            )

    def list_appointments_with_r2_sent_before(self, cutoff: datetime) -> list[dict]:
        """Citas con el recordatorio 2 enviado antes de `cutoff`."""
        rows = self._conn.execute(
            "SELECT DISTINCT a.* FROM appointments a"
            " JOIN reminders r ON r.appointment_id = a.id"
            " WHERE r.kind = 'R2' AND r.state = 'sent' AND r.sent_at <= ?",
            (_iso(cutoff),),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_upcoming_appointments(self, since: datetime) -> list[dict]:
        """Citas con inicio en o después de `since`, ordenadas por fecha."""
        rows = self._conn.execute(
            "SELECT * FROM appointments WHERE starts_at >= ? ORDER BY starts_at, id",
            (_iso(since),),
        ).fetchall()
        return [dict(row) for row in rows]

    def clear_all(self) -> None:
        """Vacía todas las tablas (para restaurar la demo)."""
        with self._conn:
            self._conn.execute("DELETE FROM replies")
            self._conn.execute("DELETE FROM reminders")
            self._conn.execute("DELETE FROM appointments")
            self._conn.execute("DELETE FROM patients")
            self._conn.execute("DELETE FROM sync_state")

    def close(self) -> None:
        self._conn.close()


def connect(path: str | Path) -> Repository:
    """Abre la base en `path` (creando carpeta y esquema) y devuelve un repositorio."""
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = ON")
    init_schema(connection)
    return Repository(connection)
