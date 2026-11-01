"""Agenda simulada del modo demo (T20).

Muestra el calendario ficticio que representa Google Calendar, con controles
para crear, mover y cancelar citas ficticias (RF-3, CA-7). Solo existe en modo
demo; en modo real la agenda se gestiona en Google Calendar.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.domain.phone import extract_phone
from app.services.planner import run_cycle
from app.web.routes import dia_legible

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


def _cycle(request: Request) -> None:
    run_cycle(
        request.app.state.calendar,
        request.app.state.repo,
        request.app.state.messaging,
        request.app.state.clock,
        clinic_tz=request.app.state.clinic_tz,
    )


def _parse_local(request: Request, date_str: str, time_str: str) -> datetime:
    """Combina fecha y hora (zona del consultorio) y las devuelve en UTC."""
    tz = request.app.state.clinic_tz
    d = datetime.fromisoformat(date_str)
    hh, mm = (int(p) for p in time_str.split(":"))
    local = datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz)
    return local.astimezone(timezone.utc)


@router.get("/agenda")
def agenda(request: Request):
    tz = request.app.state.clinic_tz
    hoy = request.app.state.clock.now().astimezone(tz).date()
    events = request.app.state.calendar.list_events()[0]

    days: dict = {}
    for e in events:
        local = e.starts_at.astimezone(tz)
        days.setdefault(local.date(), []).append(
            {
                "event_id": e.event_id,
                "patient_name": e.patient_name,
                "time": local.strftime("%H:%M"),
                "local_date": local.date().isoformat(),
                "local_time": local.strftime("%H:%M"),
                "phone": e.phone or "Sin teléfono",
            }
        )

    agenda_dias = [
        {"label": dia_legible(day, hoy), "events": items}
        for day, items in sorted(days.items())
    ]

    return templates.TemplateResponse(
        request=request,
        name="agenda.html",
        context={"agenda": agenda_dias},
    )


@router.post("/agenda/create")
def create(
    request: Request,
    patient_name: str = Form(...),
    phone: str = Form(""),
    date: str = Form(...),
    time: str = Form(...),
):
    starts_at = _parse_local(request, date, time)
    parsed_phone = extract_phone(f"Tel: {phone}") if phone.strip() else None
    request.app.state.calendar.create_event(
        patient_name=patient_name, starts_at=starts_at, phone=parsed_phone
    )
    _cycle(request)
    return RedirectResponse("/agenda", status_code=303)


@router.post("/agenda/move")
def move(
    request: Request,
    event_id: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
):
    starts_at = _parse_local(request, date, time)
    request.app.state.calendar.move_event(event_id, starts_at)
    _cycle(request)
    return RedirectResponse("/agenda", status_code=303)


@router.post("/agenda/cancel")
def cancel(request: Request, event_id: str = Form(...)):
    request.app.state.calendar.cancel_event(event_id)
    _cycle(request)
    return RedirectResponse("/agenda", status_code=303)
