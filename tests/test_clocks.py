"""Tests de los relojes (T2).

Criterio de T2: el reloj simulado avanza de forma controlada y el reloj
del sistema devuelve una hora UTC con zona horaria.
"""

from datetime import datetime, timedelta, timezone

from app.adapters.clocks import SimulatedClock, SystemClock


def test_system_clock_returns_utc_aware_datetime():
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_simulated_clock_starts_at_given_time():
    start = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    clock = SimulatedClock(start=start)
    assert clock.now() == start


def test_simulated_clock_advances_by_hours():
    start = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    clock = SimulatedClock(start=start)
    clock.advance(hours=48)
    assert clock.now() == start + timedelta(hours=48)


def test_simulated_clock_does_not_advance_on_its_own():
    start = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    clock = SimulatedClock(start=start)
    assert clock.now() == start
    assert clock.now() == start
