"""Configuración de la aplicación desde variables de entorno.

Todos los valores tienen un valor por defecto seguro para el modo demo
(constitución 13: ejecutable sin credenciales). Los secretos se leen solo
de variables de entorno y nunca se escriben en el repositorio.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Configuración cargada desde variables de entorno."""

    mode: str
    database_path: str
    clinic_timezone: str
    send_window_start: int
    send_window_end: int
    sync_interval_minutes: int
    max_send_attempts: int
    unconfirmed_after_hours: int
    panel_password: str
    session_secret: str
    google_client_id: str
    google_client_secret: str
    google_calendar_id: str
    whatsapp_phone_number_id: str
    whatsapp_access_token: str
    whatsapp_verify_token: str
    whatsapp_app_secret: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Config:
        """Construye la configuración a partir de un mapping de entorno.

        `environ` permite inyectar las variables en los tests; si es `None`,
        se usa `os.environ`.
        """
        env = os.environ if environ is None else environ
        return cls(
            mode=env.get("MODE", "demo"),
            database_path=env.get("DATABASE_PATH", "data/recordatorios.db"),
            clinic_timezone=env.get("CLINIC_TIMEZONE", "America/Bogota"),
            send_window_start=int(env.get("SEND_WINDOW_START", "8")),
            send_window_end=int(env.get("SEND_WINDOW_END", "20")),
            sync_interval_minutes=int(env.get("SYNC_INTERVAL_MINUTES", "5")),
            max_send_attempts=int(env.get("MAX_SEND_ATTEMPTS", "3")),
            unconfirmed_after_hours=int(env.get("UNCONFIRMED_AFTER_HOURS", "3")),
            panel_password=env.get("PANEL_PASSWORD", ""),
            session_secret=env.get("SESSION_SECRET", ""),
            google_client_id=env.get("GOOGLE_CLIENT_ID", ""),
            google_client_secret=env.get("GOOGLE_CLIENT_SECRET", ""),
            google_calendar_id=env.get("GOOGLE_CALENDAR_ID", ""),
            whatsapp_phone_number_id=env.get("WHATSAPP_PHONE_NUMBER_ID", ""),
            whatsapp_access_token=env.get("WHATSAPP_ACCESS_TOKEN", ""),
            whatsapp_verify_token=env.get("WHATSAPP_VERIFY_TOKEN", ""),
            whatsapp_app_secret=env.get("WHATSAPP_APP_SECRET", ""),
        )

    @property
    def is_demo(self) -> bool:
        """True si la aplicación corre en modo demo (sin servicios reales)."""
        return self.mode == "demo"
