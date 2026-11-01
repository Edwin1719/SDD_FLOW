"""Mensajería simulada para el modo demo (constitución 13)."""

from __future__ import annotations


class SimulatedMessaging:
    """Mensajería en memoria: registra los envíos y puede simular fallos."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self._fail_next = 0
        self._fail_always = False

    def send(self, to: str, body: str) -> None:
        """Registra un mensaje; lanza si se simuló un fallo."""
        if self._fail_always or self._fail_next > 0:
            if self._fail_next > 0:
                self._fail_next -= 1
            raise RuntimeError("simulated send failure")
        self.messages.append((to, body))

    def fail_next(self, count: int = 1) -> None:
        """Hace fallar los próximos `count` envíos."""
        self._fail_next = count

    def fail_always(self, value: bool = True) -> None:
        """Activa o desactiva el fallo permanente."""
        self._fail_always = value

    def clear(self) -> None:
        """Vacía los mensajes registrados."""
        self.messages.clear()
