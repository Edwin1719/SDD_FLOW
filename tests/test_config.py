"""Tests de carga de configuración (T2).

Criterio de T2: la configuración se carga con `MODE=demo` por defecto
(constitución 13: ejecutable sin credenciales).
"""

from app.config import Config


def test_config_uses_demo_mode_by_default():
    config = Config.from_env({})
    assert config.mode == "demo"
    assert config.is_demo is True


def test_config_applies_defaults():
    config = Config.from_env({})
    assert config.database_path == "data/recordatorios.db"
    assert config.clinic_timezone == "America/Bogota"
    assert config.send_window_start == 8
    assert config.send_window_end == 20
    assert config.sync_interval_minutes == 5
    assert config.max_send_attempts == 3
    assert config.unconfirmed_after_hours == 3
    assert config.panel_password == ""
    assert config.session_secret == ""


def test_config_reads_values_from_environment():
    config = Config.from_env(
        {
            "MODE": "real",
            "DATABASE_PATH": "otra/ruta.db",
            "SEND_WINDOW_START": "9",
            "SEND_WINDOW_END": "18",
            "SYNC_INTERVAL_MINUTES": "10",
            "MAX_SEND_ATTEMPTS": "5",
            "UNCONFIRMED_AFTER_HOURS": "2",
        }
    )
    assert config.mode == "real"
    assert config.is_demo is False
    assert config.database_path == "otra/ruta.db"
    assert config.send_window_start == 9
    assert config.send_window_end == 18
    assert config.sync_interval_minutes == 10
    assert config.max_send_attempts == 5
    assert config.unconfirmed_after_hours == 2
