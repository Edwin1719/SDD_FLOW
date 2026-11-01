"""Rutas del panel de la asistente (T11)."""

from __future__ import annotations

from datetime import datetime, time, timezone

import secrets
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.texts_es import ATTENTION_TITLE, AGENDA_TITLE, EMPTY_STATE, STATE_LABELS
from app.web.auth import SESSION_COOKIE, make_token, verify_token

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# Tonos y símbolos por estado (skill brand-design).
STATE_TONES = {
    "pending": "neutro",
    "reminder_sent": "neutro",
    "confirmed": "exito",
    "reschedule_requested": "atencion",
    "cancelled_by_patient": "info",
    "unconfirmed": "atencion",
    "send_error": "peligro",
    "no_consent": "neutro",
    "no_phone": "atencion",
}
STATE_SYMBOLS = {
    "pending": "○",
    "reminder_sent": "◐",
    "confirmed": "✓",
    "reschedule_requested": "↻",
    "cancelled_by_patient": "✕",
    "unconfirmed": "?",
    "send_error": "!",
    "no_consent": "⊘",
    "no_phone": "!",
}
ATTENTION_STATES = {
    "reschedule_requested",
    "cancelled_by_patient",
    "unconfirmed",
    "send_error",
    "no_phone",
}


@router.get("/")
def panel(request: Request):
    if request.app.state.mode == "real" and not _authenticated(request):
        return RedirectResponse("/login", status_code=303)
    repo = request.app.state.repo
    clinic_tz = request.app.state.clinic_tz

    now = request.app.state.clock.now()
    local_today = now.astimezone(clinic_tz).date()
    today_start = datetime.combine(local_today, time.min, tzinfo=clinic_tz)
    today_start_utc = today_start.astimezone(timezone.utc)

    attention: list[dict] = []
    days: dict = {}
    for row in repo.list_upcoming_appointments(today_start_utc):
        local = datetime.fromisoformat(row["starts_at"]).astimezone(clinic_tz)
        status = row["status"]
        view = {
            "time": local.strftime("%H:%M"),
            "name": row["patient_name"],
            "label": STATE_LABELS.get(status, status),
            "tone": STATE_TONES.get(status, "neutro"),
            "symbol": STATE_SYMBOLS.get(status, ""),
        }
        if status in ATTENTION_STATES:
            attention.append(view)
        days.setdefault(local.date(), []).append(view)

    agenda = [
        {"date": day.isoformat(), "appointments": items}
        for day, items in sorted(days.items())
    ]

    return templates.TemplateResponse(
        request=request,
        name="panel.html",
        context={
            "attention_title": ATTENTION_TITLE,
            "agenda_title": AGENDA_TITLE,
            "empty_state": EMPTY_STATE,
            "attention": attention,
            "agenda": agenda,
            "demo": request.app.state.mode == "demo",
        },
    )


def _authenticated(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    return verify_token(token, request.app.state.session_secret)


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})


@router.post("/login")
def login(request: Request, password: str = Form(...)):
    if secrets.compare_digest(password, request.app.state.panel_password):
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            SESSION_COOKIE,
            make_token(request.app.state.session_secret),
            httponly=True,
        )
        return response
    return RedirectResponse("/login", status_code=303)
