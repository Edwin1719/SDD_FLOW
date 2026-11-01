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
from app.texts_es import STATE_LABELS
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
def sim(request: Request):
    repo = request.app.state.repo
    clock = request.app.state.clock
    messaging = request.app.state.messaging

    citas = [
        {
            "id": a["id"],
            "patient_name": a["patient_name"],
            "starts_at": a["starts_at"],
            "status_label": STATE_LABELS.get(a["status"], a["status"]),
            "tone": STATE_TONES.get(a["status"], "neutro"),
            "symbol": STATE_SYMBOLS.get(a["status"], ""),
        }
        for a in repo.list_upcoming_appointments(clock.now())
    ]
    messages = [{"to": to, "body": body} for to, body in messaging.messages]

    return templates.TemplateResponse(
        request=request,
        name="sim.html",
        context={
            "now": fecha_hora_legible(clock.now().astimezone(request.app.state.clinic_tz)),
            "appointments": citas,
            "messages": messages,
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


@router.post("/sim/clock/advance")
def advance(request: Request, hours: int = Form(...)):
    request.app.state.clock.advance(hours=hours)
    _cycle(request)
    return RedirectResponse("/sim", status_code=303)


@router.post("/sim/fail-next-send")
def fail_next(request: Request):
    request.app.state.messaging.fail_next(1)
    return RedirectResponse("/sim", status_code=303)


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
