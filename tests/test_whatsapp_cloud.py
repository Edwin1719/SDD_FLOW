"""Tests del adaptador real de WhatsApp Cloud API (T15).

Usan respuestas simuladas; ninguna llamada real.
"""

from unittest.mock import MagicMock

import pytest

from app.adapters.whatsapp_cloud import TemplateMessage, WhatsAppCloud, WhatsAppError


def _adapter(client) -> WhatsAppCloud:
    return WhatsAppCloud(client, phone_number_id="12345", access_token="secret")


def test_send_builds_template_payload():
    client = MagicMock()
    client.post.return_value.status_code = 200

    _adapter(client).send(TemplateMessage(to="+573001234567", name="reminder_48h"))

    args, kwargs = client.post.call_args
    assert "12345/messages" in args[0]
    payload = kwargs["json"]
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "+573001234567"
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "reminder_48h"
    assert payload["template"]["language"] == {"code": "es"}
    assert "Authorization" in kwargs["headers"]


def test_send_raises_on_http_error():
    client = MagicMock()
    client.post.return_value.status_code = 400

    with pytest.raises(WhatsAppError):
        _adapter(client).send(TemplateMessage(to="+573001234567", name="reminder_48h"))
