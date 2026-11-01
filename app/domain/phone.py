"""Extracción y validación del teléfono (RF-1, RF-2)."""

from __future__ import annotations

import re

_TEL_LINE = re.compile(r"^Tel:\s*(.+?)\s*$", re.MULTILINE)
_PHONE = re.compile(r"\+\d{8,15}")


def extract_phone(description: str) -> str | None:
    """Extrae el teléfono de la línea `Tel:` de la descripción (RF-1, RF-2).

    Devuelve el teléfono normalizado (sin espacios, guiones ni paréntesis) si
    tiene el formato `+` seguido de 8 a 15 dígitos; si no, `None`.
    """
    if not description:
        return None
    match = _TEL_LINE.search(description)
    if match is None:
        return None
    cleaned = re.sub(r"[\s\-()]", "", match.group(1))
    return cleaned if _PHONE.fullmatch(cleaned) else None
