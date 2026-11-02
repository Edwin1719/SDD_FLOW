"""Lista de espera y espacios liberados (Spec 002), solo modo demo."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.domain.phone import extract_phone
from app.services.waitlist import (
    WaitlistError,
    candidates,
    close_slot,
    confirm_recovered,
    send_offer,
)
from app.texts_es import DIAS_SEMANA, fecha_larga

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

REASONS = ["consulta", "limpieza", "control", "tratamiento"]
REASON_LABELS = {
    "consulta": "Consulta",
    "limpieza": "Limpieza",
    "control": "Control",
    "tratamiento": "Tratamiento",
}
SLOT_LABELS = {
    "libre": "Libre",
    "ofrecido": "Oferta enviada",
    "reservado_pendiente": "Reservado pendiente",
    "recuperado": "Recuperado",
    "no_recuperado": "No recuperado",
    "ocupado": "Ocupado",
}
WAITLIST_LABELS = {
    "activa": "Activa",
    "pausada": "Pausada",
    "retirada": "Retirada",
    "sin_consentimiento": "Sin consentimiento",
    "baja": "Baja",
}
ERRORS = {
    "phone": "El teléfono no tiene un formato válido. Usa +57 seguido del número.",
    "name": "El nombre del paciente no puede estar vacío.",
    "reason": "Elige un tipo de cita válido.",
    "oferta": "No se pudo enviar la oferta. Revisa el espacio y el paciente.",
    "confirmar": "El espacio no está reservado pendiente.",
    "cerrar": "No se pudo cerrar el espacio.",
    "notfound": "No encontramos ese paciente en la lista de espera.",
}


def _slot_view(repo, slot: dict, clinic_tz) -> dict:
    starts_at = datetime.fromisoformat(slot["starts_at"])
    ends_at = datetime.fromisoformat(slot["ends_at"])
    local = starts_at.astimezone(clinic_tz)
    local_end = ends_at.astimezone(clinic_tz)
    active = repo.get_active_offer_for_slot(slot["id"])
    return {
        **slot,
        "time": local.strftime("%H:%M"),
        "end_time": local_end.strftime("%H:%M"),
        "date_label": fecha_larga(local.date()),
        "status_label": SLOT_LABELS.get(slot["status"], slot["status"]),
        "active_offer": active,
    }


def _entry_view(entry: dict, repo) -> dict:
    days = [
        DIAS_SEMANA[int(part)][:3]
        for part in (entry.get("preferred_days") or "").split(",")
        if part.strip()
    ]
    preferred = ""
    if days:
        preferred = ", ".join(days)
    start = entry.get("preferred_time_start")
    end = entry.get("preferred_time_end")
    if start and end:
        preferred = f"{preferred} · {start}–{end}" if preferred else f"{start}–{end}"
    active = repo.get_active_offer_for_entry(entry["id"])
    return {
        **entry,
        "status_label": WAITLIST_LABELS.get(entry["status"], entry["status"]),
        "preferred_label": preferred or "Sin preferencia",
        "active_offer": active,
    }


@router.get("/lista-espera")
def waitlist(
    request: Request,
    error: str | None = Query(None),
    edit: int | None = Query(None),
):
    repo = request.app.state.repo
    clinic_tz = request.app.state.clinic_tz
    all_slots = repo.list_freed_slots()
    slots = [
        _slot_view(repo, slot, clinic_tz)
        for slot in repo.list_open_freed_slots()
    ]
    recovered = sum(1 for slot in all_slots if slot["status"] == "recuperado")
    total = len(all_slots)
    metrics = {
        "recovered": recovered,
        "total": total,
        "rate": round(recovered * 100 / total) if total else 0,
    }
    entries = [_entry_view(entry, repo) for entry in repo.list_waitlist_entries()]
    edit_entry = repo.get_waitlist_entry(edit) if edit is not None else None
    selected_days: set[int] = set()
    edit_has_consent = False
    if edit_entry is not None:
        selected_days = {
            int(part)
            for part in (edit_entry.get("preferred_days") or "").split(",")
            if part.strip()
        }
        patient = repo.get_patient(edit_entry["phone"])
        edit_has_consent = bool(patient and patient["has_consent"])

    return templates.TemplateResponse(
        request=request,
        name="waitlist.html",
        context={
            "entries": entries,
            "slots": slots,
            "metrics": metrics,
            "edit_entry": edit_entry,
            "selected_days": selected_days,
            "edit_has_consent": edit_has_consent,
            "reasons": REASONS,
            "reason_labels": REASON_LABELS,
            "days": DIAS_SEMANA,
            "error": ERRORS.get(error or ""),
            "demo": True,
        },
    )


@router.post("/lista-espera/crear")
def create_entry(
    request: Request,
    patient_name: str = Form(...),
    phone: str = Form(...),
    reason: str = Form(...),
    days: list[str] = Form(default=[]),
    time_start: str = Form(""),
    time_end: str = Form(""),
    consent: str = Form(""),
):
    name = patient_name.strip()
    if not name:
        return RedirectResponse("/lista-espera?error=name", status_code=303)
    parsed_phone = extract_phone(f"Tel: {phone}") if phone.strip() else None
    if parsed_phone is None:
        return RedirectResponse("/lista-espera?error=phone", status_code=303)
    if reason not in REASONS:
        return RedirectResponse("/lista-espera?error=reason", status_code=303)

    repo = request.app.state.repo
    has_consent = bool(consent)
    repo.upsert_patient(parsed_phone, has_consent=has_consent)
    repo.create_waitlist_entry(
        patient_name=name,
        phone=parsed_phone,
        reason=reason,
        preferred_days=",".join(days),
        preferred_time_start=time_start or None,
        preferred_time_end=time_end or None,
        status="activa" if has_consent else "sin_consentimiento",
        created_at=request.app.state.clock.now(),
    )
    return RedirectResponse("/lista-espera", status_code=303)


@router.post("/lista-espera/editar")
def edit_entry(
    request: Request,
    entry_id: int = Form(...),
    patient_name: str = Form(...),
    phone: str = Form(...),
    reason: str = Form(...),
    days: list[str] = Form(default=[]),
    time_start: str = Form(""),
    time_end: str = Form(""),
    consent: str = Form(""),
):
    repo = request.app.state.repo
    entry = repo.get_waitlist_entry(entry_id)
    if entry is None:
        return RedirectResponse("/lista-espera?error=notfound", status_code=303)
    name = patient_name.strip()
    if not name:
        return RedirectResponse("/lista-espera?error=name", status_code=303)
    parsed_phone = extract_phone(f"Tel: {phone}") if phone.strip() else None
    if parsed_phone is None:
        return RedirectResponse("/lista-espera?error=phone", status_code=303)
    if reason not in REASONS:
        return RedirectResponse("/lista-espera?error=reason", status_code=303)

    has_consent = bool(consent)
    repo.upsert_patient(parsed_phone, has_consent=has_consent)
    status = entry["status"]
    if has_consent and status == "sin_consentimiento":
        status = "activa"
    elif not has_consent and status == "activa":
        status = "sin_consentimiento"
    repo.update_waitlist_entry(
        entry_id,
        patient_name=name,
        phone=parsed_phone,
        reason=reason,
        preferred_days=",".join(days),
        preferred_time_start=time_start or None,
        preferred_time_end=time_end or None,
    )
    repo.update_waitlist_status(entry_id, status)
    return RedirectResponse("/lista-espera", status_code=303)


@router.post("/lista-espera/estado")
def change_status(
    request: Request,
    entry_id: int = Form(...),
    status: str = Form(...),
):
    if status not in {"activa", "pausada", "retirada"}:
        return RedirectResponse("/lista-espera?error=name", status_code=303)
    repo = request.app.state.repo
    if repo.get_waitlist_entry(entry_id) is None:
        return RedirectResponse("/lista-espera?error=name", status_code=303)
    repo.update_waitlist_status(entry_id, status)
    return RedirectResponse("/lista-espera", status_code=303)


@router.get("/espacios/{slot_id}")
def space(request: Request, slot_id: int, error: str | None = Query(None)):
    repo = request.app.state.repo
    clinic_tz = request.app.state.clinic_tz
    slot = repo.get_freed_slot(slot_id)
    if slot is None:
        return RedirectResponse("/lista-espera", status_code=303)

    view = _slot_view(repo, slot, clinic_tz)
    now = request.app.state.clock.now()
    candidatos = (
        [
            {
                **_entry_view(item, repo),
                "score": item["score"],
                "reasons": item["reasons"],
            }
            for item in candidates(repo, slot, now=now, clinic_tz=clinic_tz)
        ]
        if slot["status"] == "libre"
        else []
    )
    active = repo.get_active_offer_for_slot(slot_id)
    active_view = None
    if active is not None:
        entry = repo.get_waitlist_entry(active["waitlist_entry_id"])
        active_view = {
            **active,
            "patient_name": entry["patient_name"] if entry else "Paciente",
            "phone": entry["phone"] if entry else "",
        }

    history = []
    for offer in repo.list_slot_offers(slot_id):
        entry = repo.get_waitlist_entry(offer["waitlist_entry_id"])
        history.append(
            {
                **offer,
                "patient_name": entry["patient_name"] if entry else "Paciente",
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="espacio.html",
        context={
            "slot": view,
            "candidates": candidatos,
            "active_offer": active_view,
            "history": history,
            "error": ERRORS.get(error or ""),
            "demo": True,
        },
    )


@router.post("/espacios/{slot_id}/ofrecer")
def offer(request: Request, slot_id: int, entry_id: int = Form(...)):
    repo = request.app.state.repo
    try:
        send_offer(
            repo,
            request.app.state.messaging,
            slot_id=slot_id,
            entry_id=entry_id,
            now=request.app.state.clock.now(),
            clinic_tz=request.app.state.clinic_tz,
        )
    except WaitlistError:
        return RedirectResponse(
            f"/espacios/{slot_id}?error=oferta", status_code=303
        )
    return RedirectResponse(f"/espacios/{slot_id}", status_code=303)


@router.post("/espacios/{slot_id}/confirmar")
def confirm(request: Request, slot_id: int):
    try:
        confirm_recovered(
            request.app.state.repo,
            slot_id=slot_id,
            now=request.app.state.clock.now(),
        )
    except WaitlistError:
        return RedirectResponse(
            f"/espacios/{slot_id}?error=confirmar", status_code=303
        )
    return RedirectResponse(f"/espacios/{slot_id}", status_code=303)


@router.post("/espacios/{slot_id}/cerrar")
def close(request: Request, slot_id: int):
    try:
        close_slot(
            request.app.state.repo,
            slot_id=slot_id,
            now=request.app.state.clock.now(),
        )
    except WaitlistError:
        return RedirectResponse(
            f"/espacios/{slot_id}?error=cerrar", status_code=303
        )
    return RedirectResponse(f"/espacios/{slot_id}", status_code=303)
