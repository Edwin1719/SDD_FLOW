"""Agenda simulada del modo demo (T20).

Vista de día que representa Google Calendar: crear, mover, editar y cancelar
citas ficticias. Solo existe en modo demo (RF-3, RF-18).
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.domain.phone import extract_phone
from app.services.planner import run_cycle
from app.texts_es import DIAS_SEMANA, fecha_larga
from app.web.routes import STATE_LABELS, STATE_SYMBOLS, STATE_TONES, _slot_view

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

_ERRORS = {
    "phone": "El teléfono no tiene un formato válido. Usa +57 seguido del número.",
    "name": "El nombre del paciente no puede estar vacío.",
    "notfound": "No encontramos esa cita. Actualiza la agenda e inténtalo de nuevo.",
}


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


def _view(request: Request, event) -> dict:
    tz = request.app.state.clinic_tz
    local = event.starts_at.astimezone(tz)
    appointment = request.app.state.repo.get_appointment(event.event_id)
    status = appointment["status"] if appointment is not None else "pending"
    return {
        "event_id": event.event_id,
        "appointment_id": appointment["id"] if appointment is not None else None,
        "name": event.patient_name,
        "phone": event.phone,
        "phone_label": event.phone or "Sin teléfono",
        "time": local.strftime("%H:%M"),
        "local_date": local.date().isoformat(),
        "date_value": local.date().isoformat(),
        "time_value": local.strftime("%H:%M"),
        "status": status,
        "label": STATE_LABELS.get(status, status),
        "tone": STATE_TONES.get(status, "neutro"),
        "symbol": STATE_SYMBOLS.get(status, ""),
        "out_of_hours": local.hour < 8 or local.hour >= 20,
    }


@router.get("/agenda")
def agenda(
    request: Request,
    date_str: str | None = Query(None, alias="date"),
    edit: int | None = Query(None),
    error: str | None = Query(None),
):
    tz = request.app.state.clinic_tz
    today = request.app.state.clock.now().astimezone(tz).date()
    try:
        selected = date_cls.fromisoformat(date_str) if date_str else today
    except ValueError:
        selected = today

    events = request.app.state.calendar.list_events()[0]
    day_events = [_view(request, e) for e in events]
    day_events = [e for e in day_events if e["local_date"] == selected.isoformat()]
    day_events.sort(key=lambda e: e["time"])
    within = [e for e in day_events if not e["out_of_hours"]]
    outside = [e for e in day_events if e["out_of_hours"]]

    week_start = selected - timedelta(days=selected.weekday())
    days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        if d == today:
            label = "Hoy"
        elif d == today + timedelta(days=1):
            label = "Mañana"
        else:
            label = f"{DIAS_SEMANA[d.weekday()][:3].capitalize()} {d.day}"
        days.append(
            {
                "date": d.isoformat(),
                "label": label,
                "active": d == selected,
            }
        )

    slots = [
        _slot_view(slot, tz)
        for slot in request.app.state.repo.list_open_freed_slots()
    ]

    edit_event = None
    if edit is not None:
        appointment = request.app.state.repo.get_appointment_by_id(edit)
        if appointment is not None:
            local = datetime.fromisoformat(appointment["starts_at"]).astimezone(tz)
            patient = (
                request.app.state.repo.get_patient(appointment["phone"])
                if appointment["phone"]
                else None
            )
            edit_event = {
                "appointment_id": appointment["id"],
                "event_id": appointment["event_id"],
                "patient_name": appointment["patient_name"],
                "phone": appointment["phone"] or "",
                "date": local.date().isoformat(),
                "time": local.strftime("%H:%M"),
                "has_consent": bool(patient and patient["has_consent"]),
            }

    return templates.TemplateResponse(
        request=request,
        name="agenda.html",
        context={
            "selected_date": selected.isoformat(),
            "selected_label": fecha_larga(selected),
            "slots": slots,
            "today_label": fecha_larga(today),
            "days": days,
            "events": within,
            "out_of_hours": outside,
            "empty": len(day_events) == 0,
            "edit_event": edit_event,
            "error": _ERRORS.get(error or ""),
            "demo": True,
        },
    )


@router.post("/agenda/create")
def create(
    request: Request,
    patient_name: str = Form(...),
    phone: str = Form(""),
    date: str = Form(...),
    time: str = Form(...),
    consent: str = Form(""),
):
    name = patient_name.strip()
    if not name:
        return RedirectResponse("/agenda?error=name", status_code=303)
    parsed_phone = extract_phone(f"Tel: {phone}") if phone.strip() else None
    if phone.strip() and parsed_phone is None:
        return RedirectResponse("/agenda?error=phone", status_code=303)

    if consent and parsed_phone:
        request.app.state.repo.upsert_patient(parsed_phone, has_consent=True)

    starts_at = _parse_local(request, date, time)
    request.app.state.calendar.create_event(
        patient_name=name, starts_at=starts_at, phone=parsed_phone
    )
    _cycle(request)
    local_date = starts_at.astimezone(request.app.state.clinic_tz).date().isoformat()
    return RedirectResponse(f"/agenda?date={local_date}", status_code=303)


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
    local_date = starts_at.astimezone(request.app.state.clinic_tz).date().isoformat()
    return RedirectResponse(f"/agenda?date={local_date}", status_code=303)


@router.post("/agenda/edit")
def edit(
    request: Request,
    appointment_id: int = Form(...),
    patient_name: str = Form(...),
    phone: str = Form(""),
    date: str = Form(...),
    time: str = Form(...),
    consent: str = Form(""),
):
    repo = request.app.state.repo
    appointment = repo.get_appointment_by_id(appointment_id)
    if appointment is None:
        return RedirectResponse("/agenda?error=notfound", status_code=303)

    name = patient_name.strip()
    if not name:
        return RedirectResponse(
            f"/agenda?date={date}&edit={appointment_id}&error=name", status_code=303
        )

    parsed_phone = extract_phone(f"Tel: {phone}") if phone.strip() else None
    if phone.strip() and parsed_phone is None:
        return RedirectResponse(
            f"/agenda?date={date}&edit={appointment_id}&error=phone", status_code=303
        )

    if consent and parsed_phone:
        existing_patient = repo.get_patient(parsed_phone)
        repo.upsert_patient(
            parsed_phone,
            has_consent=True,
            opted_out=bool(existing_patient and existing_patient["opted_out"]),
        )

    starts_at = _parse_local(request, date, time)
    updated = request.app.state.calendar.update_event(
        appointment["event_id"],
        patient_name=name,
        phone=parsed_phone,
        starts_at=starts_at,
    )
    if not updated:
        return RedirectResponse("/agenda?error=notfound", status_code=303)

    _cycle(request)
    local_date = starts_at.astimezone(request.app.state.clinic_tz).date().isoformat()
    return RedirectResponse(f"/agenda?date={local_date}", status_code=303)


@router.post("/agenda/cancel")
def cancel(request: Request, event_id: str = Form(...)):
    request.app.state.calendar.cancel_event(event_id)
    _cycle(request)
    return RedirectResponse("/agenda", status_code=303)
