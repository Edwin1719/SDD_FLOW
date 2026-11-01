"""Webhook de WhatsApp: verificación inicial y comprobación de firma (T15)."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import PlainTextResponse

router = APIRouter()


def verify_signature(body: bytes, signature: str | None, app_secret: str) -> bool:
    """Verifica la firma `X-Hub-Signature-256` del webhook (HMAC-SHA256)."""
    if not signature or not signature.startswith("sha256="):
        return False
    digest = signature.removeprefix("sha256=")
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, digest)


@router.get("/webhooks/whatsapp")
def verify(
    request: Request,
    mode: str = Query(alias="hub.mode"),
    verify_token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    """Verificación inicial de Meta: devuelve el challenge si el token coincide."""
    if mode == "subscribe" and verify_token == request.app.state.whatsapp_verify_token:
        return PlainTextResponse(challenge)
    return Response(status_code=403)


@router.post("/webhooks/whatsapp")
async def receive(request: Request):
    """Recepción de respuestas: rechaza si la firma no es válida."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(body, signature, request.app.state.whatsapp_app_secret):
        return Response(status_code=403)
    return Response(status_code=200)
