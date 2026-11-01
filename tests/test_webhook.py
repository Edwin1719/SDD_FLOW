"""Tests del webhook de WhatsApp (T15)."""

import hashlib
import hmac

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.web.webhook import router, verify_signature

SECRET = "app-secret"
TOKEN = "verify-token"


def _sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _make_app() -> FastAPI:
    app = FastAPI()
    app.state.whatsapp_verify_token = TOKEN
    app.state.whatsapp_app_secret = SECRET
    app.include_router(router)
    return app


def test_verify_signature_valid():
    body = b'{"object":"whatsapp_business_account"}'
    assert verify_signature(body, _sign(body), SECRET) is True


def test_verify_signature_invalid():
    body = b'{"object":"whatsapp_business_account"}'
    assert verify_signature(body, _sign(b"otro"), SECRET) is False


def test_verify_signature_missing():
    assert verify_signature(b"x", None, SECRET) is False


def test_get_verification_returns_challenge():
    client = TestClient(_make_app())
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": TOKEN,
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


def test_get_verification_rejects_bad_token():
    client = TestClient(_make_app())
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


def test_post_rejects_invalid_signature():
    client = TestClient(_make_app())
    response = client.post(
        "/webhooks/whatsapp",
        content=b'{"object":"whatsapp_business_account"}',
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert response.status_code == 403
