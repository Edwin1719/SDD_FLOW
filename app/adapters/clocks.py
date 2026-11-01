"""Relojes: implementaciones de `ClockPort` para producción y demo."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.ports.clock import ClockPort


class SystemClock(ClockPort):
    """Reloj real: la hora del sistema, en UTC."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class SimulatedClock(ClockPort):
    """Reloj de la demo: la hora solo avanza cuando se le ordena explícitamente."""

    def __init__(self, start: datetime | None = None) -> None:
        self._current = start if start is not None else datetime.now(timezone.utc)

    def now(self) -> datetime:
        return self._current

    def advance(
        self,
        *,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
    ) -> datetime:
        """Avanza el reloj la cantidad indicada y devuelve la nueva hora."""
        self._current += timedelta(
            seconds=seconds, minutes=minutes, hours=hours, days=days
        )
        return self._current

    def reset(self, start: datetime | None = None) -> None:
        """Reinicia el reloj a `start` (o a la hora actual)."""
        self._current = start if start is not None else datetime.now(timezone.utc)
