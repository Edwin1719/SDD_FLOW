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
        ends_at: datetime | None = None,
    ) -> int:
        """Inserta una cita y devuelve su id."""
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO appointments
                    (event_id, patient_name, phone, starts_at, ends_at,
                     status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    patient_name,
                    phone,
                    _iso(starts_at),
                    _iso(ends_at) if ends_at is not None else None,
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
        ends_at: datetime | None = None,
    ) -> None:
        """Actualiza nombre, teléfono, fecha, duración y estado (RF-18)."""
        with self._conn:
            self._conn.execute(
                "UPDATE appointments SET patient_name = ?, phone = ?,"
                " starts_at = ?, ends_at = ?, status = ?, updated_at = ?"
                " WHERE id = ?",
                (
                    patient_name,
                    phone,
                    _iso(starts_at),
                    _iso(ends_at) if ends_at is not None else None,
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

    def create_waitlist_entry(
        self,
        *,
        patient_name: str,
        phone: str,
        reason: str,
        preferred_days: str,
        preferred_time_start: str | None,
        preferred_time_end: str | None,
        status: str,
        created_at: datetime,
        source: str = "asistente",
    ) -> int:
        """Registra una entrada de lista de espera y devuelve su id."""
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO waitlist_entries
                    (patient_name, phone, reason, preferred_days,
                     preferred_time_start, preferred_time_end, source,
                     created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_name,
                    phone,
                    reason,
                    preferred_days,
                    preferred_time_start,
                    preferred_time_end,
                    source,
                    _iso(created_at),
                    status,
                ),
            )
        return cursor.lastrowid

    def get_waitlist_entry(self, entry_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM waitlist_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def list_waitlist_entries(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM waitlist_entries ORDER BY created_at, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def list_active_waitlist_entries(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM waitlist_entries WHERE status = 'activa'"
            " ORDER BY created_at, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def update_waitlist_status(self, entry_id: int, status: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE waitlist_entries SET status = ? WHERE id = ?",
                (status, entry_id),
            )

    def update_waitlist_entry(
        self,
        entry_id: int,
        *,
        patient_name: str,
        phone: str,
        reason: str,
        preferred_days: str,
        preferred_time_start: str | None,
        preferred_time_end: str | None,
    ) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE waitlist_entries SET patient_name = ?, phone = ?,"
                " reason = ?, preferred_days = ?, preferred_time_start = ?,"
                " preferred_time_end = ? WHERE id = ?",
                (
                    patient_name,
                    phone,
                    reason,
                    preferred_days,
                    preferred_time_start,
                    preferred_time_end,
                    entry_id,
                ),
            )

    def mark_waitlist_offered(self, entry_id: int, when: datetime) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE waitlist_entries SET last_offered_at = ? WHERE id = ?",
                (_iso(when), entry_id),
            )

    def count_offers_for_entry_since(self, entry_id: int, since: datetime) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM slot_offers"
            " WHERE waitlist_entry_id = ? AND sent_at >= ?",
            (entry_id, _iso(since)),
        ).fetchone()
        return int(row[0])

    def create_freed_slot(
        self,
        *,
        event_id: str,
        starts_at: datetime,
        ends_at: datetime,
        duration_estimated: bool,
        source: str,
        created_at: datetime,
    ) -> int | None:
        """Crea un espacio liberado; si ya existe, devuelve su id."""
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT OR IGNORE INTO freed_slots
                    (event_id, starts_at, ends_at, duration_estimated,
                     source, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'libre')
                """,
                (
                    event_id,
                    _iso(starts_at),
                    _iso(ends_at),
                    int(duration_estimated),
                    source,
                    _iso(created_at),
                ),
            )
        if cursor.rowcount:
            return cursor.lastrowid
        row = self._conn.execute(
            "SELECT id FROM freed_slots"
            " WHERE event_id = ? AND starts_at = ? AND ends_at = ?",
            (event_id, _iso(starts_at), _iso(ends_at)),
        ).fetchone()
        return int(row[0]) if row is not None else None

    def get_freed_slot(self, slot_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM freed_slots WHERE id = ?", (slot_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def list_freed_slots(self, status: str | None = None) -> list[dict]:
        if status is None:
            rows = self._conn.execute(
                "SELECT * FROM freed_slots ORDER BY starts_at, id"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM freed_slots WHERE status = ?"
                " ORDER BY starts_at, id",
                (status,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_open_freed_slots(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM freed_slots"
            " WHERE status IN ('libre', 'ofrecido', 'reservado_pendiente')"
            " ORDER BY starts_at, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def set_freed_slot_status(
        self,
        slot_id: int,
        status: str,
        *,
        recovered_at: datetime | None = None,
    ) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE freed_slots SET status = ?, recovered_at = ? WHERE id = ?",
                (
                    status,
                    _iso(recovered_at) if recovered_at is not None else None,
                    slot_id,
                ),
            )

    def has_appointment_at(self, starts_at: datetime) -> bool:
        """True si ya hay una cita local que ocupa ese inicio."""
        row = self._conn.execute(
            "SELECT 1 FROM appointments WHERE starts_at = ? LIMIT 1",
            (_iso(starts_at),),
        ).fetchone()
        return row is not None

    def has_appointment_for_phone_at(
        self, phone: str, starts_at: datetime
    ) -> bool:
        """True si el paciente ya tiene una cita en ese inicio."""
        row = self._conn.execute(
            "SELECT 1 FROM appointments WHERE phone = ? AND starts_at = ? LIMIT 1",
            (phone, _iso(starts_at)),
        ).fetchone()
        return row is not None

    def create_slot_offer(
        self,
        *,
        freed_slot_id: int,
        waitlist_entry_id: int,
        sent_at: datetime,
        expires_at: datetime,
    ) -> int:
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO slot_offers
                    (freed_slot_id, waitlist_entry_id, sent_at, expires_at, status)
                VALUES (?, ?, ?, ?, 'enviada')
                """,
                (
                    freed_slot_id,
                    waitlist_entry_id,
                    _iso(sent_at),
                    _iso(expires_at),
                ),
            )
        return cursor.lastrowid

    def get_slot_offer(self, offer_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM slot_offers WHERE id = ?", (offer_id,)
        ).fetchone()
        return dict(row) if row is not None else None

    def get_active_offer_for_slot(self, slot_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM slot_offers WHERE freed_slot_id = ?"
            " AND status = 'enviada' LIMIT 1",
            (slot_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def get_active_offer_for_entry(self, entry_id: int) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM slot_offers WHERE waitlist_entry_id = ?"
            " AND status = 'enviada' LIMIT 1",
            (entry_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def list_slot_offers(self, slot_id: int) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM slot_offers WHERE freed_slot_id = ? ORDER BY id",
            (slot_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_sent_offers(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM slot_offers WHERE status = 'enviada'"
            " ORDER BY expires_at, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def update_slot_offer(
        self,
        offer_id: int,
        *,
        status: str,
        response: str | None = None,
        responded_at: datetime | None = None,
    ) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE slot_offers SET status = ?, response = ?, responded_at = ?"
                " WHERE id = ?",
                (
                    status,
                    response,
                    _iso(responded_at) if responded_at is not None else None,
                    offer_id,
                ),
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
            self._conn.execute("DELETE FROM slot_offers")
            self._conn.execute("DELETE FROM freed_slots")
            self._conn.execute("DELETE FROM waitlist_entries")
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
