"""Puerto de mensajería: envío de mensajes por WhatsApp (constitución 5)."""

from __future__ import annotations

from typing import Protocol


class MessagingPort(Protocol):
    """Canal de envío (WhatsApp Cloud API en real, SimulatedMessaging en demo)."""

    def send(self, to: str, body: str) -> None:
        """Envía un mensaje a un teléfono.

        Lanza una excepción si el envío falla; el servicio de envío se encarga
        de los reintentos y de marcar Error de envío al agotarlos (RF-16).
        """
        ...
