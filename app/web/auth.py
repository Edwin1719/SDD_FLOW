"""Autenticación del panel (cookie de sesión firmada, solo modo real)."""

from __future__ import annotations

import hashlib
import hmac

SESSION_COOKIE = "session"
_SESSION_VALUE = "ok"


def _sign(value: str, secret: str) -> str:
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def make_token(secret: str) -> str:
    """Crea un token de sesión firmado."""
    return _sign(_SESSION_VALUE, secret)


def verify_token(token: str | None, secret: str) -> bool:
    """Verifica el token de sesión firmado."""
    return token is not None and hmac.compare_digest(
        token, _sign(_SESSION_VALUE, secret)
    )
