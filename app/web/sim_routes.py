"""Controles del simulador (solo modo demo)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.demo_seed import reset_demo
from app.domain.models import ReplyAction
from app.services.planner import run_cycle
from app.services.replies import apply_button_reply, apply_optout
from app.services.waitlist import WaitlistError, respond_offer
from app.texts_es import STATE_LABELS, fecha_larga
from app.web.routes import STATE_SYMBOLS, STATE_TONES, fecha_hora_legible

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


@router.get("/sim")
def sim(request: Request, fallo: int = 0, error: str | None = None):
    repo = request.app.state.repo
    clock = request.app.state.clock
    messaging = request.app.state.messaging
    clinic_tz = request.app.state.clinic_tz

    appointments = list(repo.list_upcoming_appointments(clock.now()))
    names_by_phone = {
        a["phone"]: a["patient_name"]
        for a in repo.list_appointments()
        if a["phone"]
    }
    citas = []
    for a in appointments:
        patient = repo.get_patient(a["phone"]) if a["phone"] else None
        can_reply = bool(
            a["phone"]
            and patient is not None
            and patient["has_consent"]
            and not patient["opted_out"]
        )
        if a["phone"] is None:
            reason = "Sin teléfono: no se le puede enviar ni responder."
        elif patient is None or not patient["has_consent"]:
            reason = "Sin consentimiento: no se le envían mensajes."
        elif patient["opted_out"]:
            reason = "El paciente pidió la baja: no se le envían mensajes."
        else:
            reason = ""
        citas.append(
            {
                "id": a["id"],
                "patient_name": a["patient_name"],
                "starts_at": a["starts_at"],
                "status_label": STATE_LABELS.get(a["status"], a["status"]),
                "tone": STATE_TONES.get(a["status"], "neutro"),
                "symbol": STATE_SYMBOLS.get(a["status"], ""),
                "can_reply": can_reply,
                "reason": reason,
            }
        )

    messages = [
        {"to": to, "body": body, "name": names_by_phone.get(to, to)}
        for to, body in messaging.messages
    ]

    offers = []
    for offer in repo.list_sent_offers():
        slot = repo.get_freed_slot(offer["freed_slot_id"])
        entry = repo.get_waitlist_entry(offer["waitlist_entry_id"])
        if slot is None or entry is None:
            continue
        local = datetime.fromisoformat(slot["starts_at"]).astimezone(clinic_tz)
        offers.append(
            {
                **offer,
                "patient_name": entry["patient_name"],
                "slot_label": f"{fecha_larga(local.date())}, "
                f"{local.strftime('%H:%M')}–"
                f"{datetime.fromisoformat(slot['ends_at']).astimezone(clinic_tz).strftime('%H:%M')}",
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="sim.html",
        context={
            "now": fecha_hora_legible(
                clock.now().astimezone(request.app.state.clinic_tz)
            ),
            "appointments": citas,
            "messages": messages,
            "offers": offers,
            "fallo": bool(fallo),
            "error": (
                "No se pudo responder la oferta. Revisa el estado del espacio."
                if error
                else None
            ),
        },
    )


@router.post("/sim/reply")
def reply(
    request: Request,
    appointment_id: int = Form(...),
    starts_at: str = Form(...),
    action: str = Form(...),
):
    repo = request.app.state.repo
    messaging = request.app.state.messaging
    clock = request.app.state.clock
    original_starts_at = datetime.fromisoformat(starts_at)
    received_at = clock.now()

    if action == "optout":
        apply_optout(repo, appointment_id=appointment_id, received_at=received_at)
    else:
        apply_button_reply(
            repo,
            messaging,
            appointment_id=appointment_id,
            action=ReplyAction(action),
            original_starts_at=original_starts_at,
            received_at=received_at,
        )
    return RedirectResponse("/sim", status_code=303)


@router.post("/panel/reply")
def panel_reply(
    request: Request,
    appointment_id: int = Form(...),
    starts_at: str = Form(...),
    action: str = Form(...),
):
    repo = request.app.state.repo
    messaging = request.app.state.messaging
    clock = request.app.state.clock
    original_starts_at = datetime.fromisoformat(starts_at)
    received_at = clock.now()

    if action == "optout":
        apply_optout(repo, appointment_id=appointment_id, received_at=received_at)
    else:
        apply_button_reply(
            repo,
            messaging,
            appointment_id=appointment_id,
            action=ReplyAction(action),
            original_starts_at=original_starts_at,
            received_at=received_at,
        )
    return RedirectResponse("/", status_code=303)


@router.post("/sim/offer/reply")
def offer_reply(
    request: Request,
    offer_id: int = Form(...),
    action: str = Form(...),
):
    try:
        respond_offer(
            request.app.state.repo,
            request.app.state.messaging,
            offer_id=offer_id,
            action=action,
            now=request.app.state.clock.now(),
            clinic_tz=request.app.state.clinic_tz,
        )
    except WaitlistError:
        return RedirectResponse("/sim?error=oferta", status_code=303)
    return RedirectResponse("/sim", status_code=303)


@router.post("/sim/clock/advance")
def advance(request: Request, hours: int = Form(...)):
    request.app.state.clock.advance(hours=hours)
    _cycle(request)
    return RedirectResponse("/sim", status_code=303)


@router.post("/sim/fail-next-send")
def fail_next(request: Request):
    request.app.state.messaging.fail_next(1)
    return RedirectResponse("/sim?fallo=1", status_code=303)


@router.post("/sim/reset")
def reset(request: Request):
    reset_demo(
        request.app.state.repo,
        request.app.state.calendar,
        request.app.state.clock,
        request.app.state.messaging,
        clinic_tz=request.app.state.clinic_tz,
    )
    return RedirectResponse("/sim", status_code=303)
