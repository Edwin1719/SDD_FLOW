"""Adaptador real de WhatsApp Cloud API (envío de plantillas)."""

from __future__ import annotations

from dataclasses import dataclass, field


class WhatsAppError(RuntimeError):
    """Fallo al enviar un mensaje por WhatsApp."""


@dataclass(frozen=True)
class TemplateMessage:
    """Mensaje de plantilla aprobada por Meta."""

    to: str
    name: str  # nombre de la plantilla (reminder_48h, reminder_24h, ...)
    components: list[dict] = field(default_factory=list)
    language: str = "es"


class WhatsAppCloud:
    """Envía mensajes de plantilla por la Cloud API de WhatsApp."""

    def __init__(self, client, *, phone_number_id: str, access_token: str) -> None:
        self._client = client
        self._phone_number_id = phone_number_id
        self._access_token = access_token

    def send(self, message: TemplateMessage) -> None:
        """Envía una plantilla; lanza `WhatsAppError` si la API responde con error."""
        response = self._client.post(
            f"https://graph.facebook.com/v18.0/{self._phone_number_id}/messages",
            headers={"Authorization": f"Bearer {self._access_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": message.to,
                "type": "template",
                "template": {
                    "name": message.name,
                    "language": {"code": message.language},
                    "components": message.components,
                },
            },
        )
        if response.status_code >= 400:
            raise WhatsAppError(f"envío falló: HTTP {response.status_code}")
