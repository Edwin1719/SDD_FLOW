"""Rutas del panel de la asistente (T11)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import secrets

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.texts_es import (
    ATTENTION_TITLE,
    EMPTY_STATE,
    STATE_LABELS,
    fecha_larga,
)
from app.web.auth import SESSION_COOKIE, make_token, verify_token

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# Tonos y símbolos por estado (skill brand-design).
STATE_TONES = {
    "pending": "neutro",
    "reminder_sent": "neutro",
    "confirmed": "exito",
    "reschedule_requested": "atencion",
    "cancelled_by_patient": "morado",
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
    "no_consent",
    "no_phone",
}


def dia_legible(day: date, hoy: date) -> str:
    """Etiqueta del día: «Hoy», «Mañana» o «Lunes 3 de noviembre»."""
    if day == hoy:
        return "Hoy"
    if day == hoy + timedelta(days=1):
        return "Mañana"
    return fecha_larga(day)


def fecha_hora_legible(momento: datetime) -> str:
    """Fecha y hora en español: «Lunes 3 de noviembre, 14:30»."""
    return f"{fecha_larga(momento.date())}, {momento.strftime('%H:%M')}"


def _view(row: dict, clinic_tz) -> dict:
    """Vista de una cita para el panel y la agenda."""
    local = datetime.fromisoformat(row["starts_at"]).astimezone(clinic_tz)
    status = row["status"]
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "time": local.strftime("%H:%M"),
        "name": row["patient_name"],
        "phone": row["phone"],
        "status": status,
        "label": STATE_LABELS.get(status, status),
        "tone": STATE_TONES.get(status, "neutro"),
        "symbol": STATE_SYMBOLS.get(status, ""),
        "local_date": local.date().isoformat(),
        "date_label": fecha_larga(local.date()),
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

    rows = list(repo.list_upcoming_appointments(today_start_utc))

    attention: list[dict] = []
    today_rows: list[dict] = []
    all_rows: list[dict] = []
    citas_hoy = 0
    confirmadas_hoy = 0

    for row in rows:
        view = _view(row, clinic_tz)
        all_rows.append(view)
        if view["local_date"] == local_today.isoformat():
            citas_hoy += 1
            if view["status"] == "confirmed":
                confirmadas_hoy += 1
            today_rows.append(view)
        if view["status"] in ATTENTION_STATES:
            attention.append(view)

    if today_rows:
        agenda_title = "Agenda de hoy"
        agenda_rows = today_rows
    else:
        agenda_title = "Próximas citas"
        agenda_rows = all_rows

    resumen = [
        {
            "etiqueta": "Citas hoy",
            "numero": citas_hoy,
            "secundaria": "en la agenda",
        },
        {
            "etiqueta": "Atención",
            "numero": len(attention),
            "secundaria": "requieren revisión",
        },
        {
            "etiqueta": "Confirmadas",
            "numero": confirmadas_hoy,
            "secundaria": "hoy",
        },
    ]

    return templates.TemplateResponse(
        request=request,
        name="panel.html",
        context={
            "attention_title": ATTENTION_TITLE,
            "empty_state": EMPTY_STATE,
            "attention": attention,
            "agenda_title": agenda_title,
            "agenda_rows": agenda_rows,
            "empty_agenda": len(agenda_rows) == 0,
            "resumen": resumen,
            "hoy_label": fecha_larga(local_today),
            "empty": len(rows) == 0,
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
