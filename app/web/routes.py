"""Rutas del panel de la asistente (T11)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import secrets
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.texts_es import ATTENTION_TITLE, EMPTY_STATE, STATE_LABELS
from app.web.auth import SESSION_COOKIE, make_token, verify_token

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# Nombres de días y meses en español para fechas legibles (constitución 12).
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def dia_legible(day: date, hoy: date) -> str:
    """Etiqueta del día: «Hoy», «Mañana» o «Lunes 3 de noviembre»."""
    if day == hoy:
        return "Hoy"
    if day == hoy + timedelta(days=1):
        return "Mañana"
    return f"{DIAS_SEMANA[day.weekday()].capitalize()} {day.day} de {MESES[day.month - 1]}"


def fecha_hora_legible(momento: datetime) -> str:
    """Fecha y hora en español: «Lunes 3 de noviembre, 14:30»."""
    d = momento.date()
    nombre = f"{DIAS_SEMANA[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]}"
    return f"{nombre}, {momento.strftime('%H:%M')}"

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

    rows = list(repo.list_upcoming_appointments(today_start_utc))

    attention: list[dict] = []
    citas_hoy = 0
    confirmadas_hoy = 0

    dias: list[str] = []
    for i in range(7):
        d = local_today + timedelta(days=i)
        if i == 0:
            dias.append("Hoy")
        elif i == 1:
            dias.append("Mañana")
        else:
            dias.append(f"{DIAS_SEMANA[d.weekday()][:3].capitalize()} {d.day}")

    horas = [f"{h:02d}:00" for h in range(8, 21)]  # 8:00 a 20:00
    celdas: list[list[list[dict]]] = [[[] for _ in range(7)] for _ in range(len(horas))]

    for row in rows:
        local = datetime.fromisoformat(row["starts_at"]).astimezone(clinic_tz)
        status = row["status"]
        if local.date() == local_today:
            citas_hoy += 1
            if status == "confirmed":
                confirmadas_hoy += 1

        view = {
            "time": local.strftime("%H:%M"),
            "name": row["patient_name"],
            "label": STATE_LABELS.get(status, status),
            "tone": STATE_TONES.get(status, "neutro"),
            "symbol": STATE_SYMBOLS.get(status, ""),
        }
        if status in ATTENTION_STATES:
            attention.append(view)

        day_index = (local.date() - local_today).days
        if 0 <= day_index < 7:
            hour_index = max(0, min(local.hour - 8, len(horas) - 1))
            celdas[hour_index][day_index].append(
                {
                    **view,
                    "appointment_id": row["id"],
                    "starts_at": row["starts_at"],
                }
            )

    resumen = [
        {"etiqueta": "Citas hoy", "numero": citas_hoy, "secundaria": "en la agenda"},
        {"etiqueta": "Requieren atención", "numero": len(attention), "secundaria": "para revisar"},
        {"etiqueta": "Confirmadas hoy", "numero": confirmadas_hoy, "secundaria": "pacientes confirmados"},
    ]

    return templates.TemplateResponse(
        request=request,
        name="panel.html",
        context={
            "attention_title": ATTENTION_TITLE,
            "empty_state": EMPTY_STATE,
            "attention": attention,
            "resumen": resumen,
            "dias": dias,
            "horas": horas,
            "celdas": celdas,
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
