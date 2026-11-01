"""Puerto del reloj: abstracción del tiempo para la lógica y la demo.

Constitución 7: la lógica de negocio no depende del reloj real. Se inyecta
una implementación de `ClockPort` (`SystemClock` en producción,
`SimulatedClock` en la demo).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Fuente de tiempo inyectable."""

    def now(self) -> datetime:
        """Hora actual, con zona horaria (UTC)."""
        ...
