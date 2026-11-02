"""Lista de espera y recuperación de espacios liberados (Spec 003).

Lógica de aplicación: matching, oferta, respuesta y cierre. No escribe en
Google Calendar; la asistente mueve o crea la cita y confirma en la app.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, tzinfo

from app.db.repository import Repository
from app.ports.messaging import MessagingPort
from app.texts_es import SLOT_ACCEPTED, SLOT_DECLINED, format_slot_offer

DEFAULT_TTL_MINUTES = 30
NEAR_SLOT_TTL_MINUTES = 15
NEAR_SLOT_HOURS = 2
DEFAULT_MAX_OFFERS_PER_WEEK = 2
MAX_OFFERS_HARD_CAP = 3


class WaitlistError(ValueError):
    """Error de negocio de la lista de espera."""


def _days(value: str) -> set[int]:
    return {int(part) for part in value.split(",") if part.strip()}


def _in_window(now: datetime, clinic_tz: tzinfo) -> bool:
    local = now.astimezone(clinic_tz)
    return time(8, 0) <= local.time() < time(20, 0)


def _score(entry: dict, starts_at: datetime, clinic_tz: tzinfo, now: datetime):
    local = starts_at.astimezone(clinic_tz)
    score = 0
    reasons: list[str] = []

    preferred_days = _days(entry.get("preferred_days") or "")
    if preferred_days and local.weekday() in preferred_days:
        score += 3
        reasons.append("prefiere ese día")

    start = entry.get("preferred_time_start")
    end = entry.get("preferred_time_end")
    if start and end and start <= local.strftime("%H:%M") < end:
        score += 2
        reasons.append("prefiere esa franja")

    created = datetime.fromisoformat(entry["created_at"])
    weeks = max(0, (now - created).days // 7)
    if weeks:
        score += min(weeks, 3)
        reasons.append(f"espera desde hace {max(1, (now - created).days)} días")

    return score, reasons


def candidates(
    repo: Repository,
    slot: dict,
    *,
    now: datetime,
    clinic_tz: tzinfo,
    limit: int = 3,
    max_offers_per_week: int = DEFAULT_MAX_OFFERS_PER_WEEK,
) -> list[dict]:
    """Devuelve hasta limit candidatos elegibles, ordenados por match."""
    starts_at = datetime.fromisoformat(slot["starts_at"])
    since = now - timedelta(days=7)
    result: list[dict] = []

    for entry in repo.list_active_waitlist_entries():
        patient = repo.get_patient(entry["phone"])
        if patient is None or not patient["has_consent"] or patient["opted_out"]:
            continue
        if repo.get_active_offer_for_entry(entry["id"]) is not None:
            continue
        if repo.count_offers_for_entry_since(entry["id"], since) >= max_offers_per_week:
            continue
        if repo.has_appointment_for_phone_at(entry["phone"], starts_at):
            continue
        score, reasons = _score(entry, starts_at, clinic_tz, now)
        result.append({**entry, "score": score, "reasons": reasons})

    result.sort(key=lambda item: (-item["score"], item["created_at"], item["id"]))
    return result[:limit]


def send_offer(
    repo: Repository,
    messaging: MessagingPort,
    *,
    slot_id: int,
    entry_id: int,
    now: datetime,
    clinic_tz: tzinfo,
    max_offers_per_week: int = DEFAULT_MAX_OFFERS_PER_WEEK,
) -> dict:
    """Envía una oferta a un candidato; una sola oferta activa por espacio."""
    if max_offers_per_week > MAX_OFFERS_HARD_CAP:
        raise WaitlistError("El máximo de ofertas no puede superar 3.")
    if not _in_window(now, clinic_tz):
        raise WaitlistError("Fuera de la ventana de envío de 8:00 a 20:00.")

    slot = repo.get_freed_slot(slot_id)
    if slot is None or slot["status"] != "libre":
        raise WaitlistError("El espacio no está libre.")
    if repo.get_active_offer_for_slot(slot_id) is not None:
        raise WaitlistError("Ya hay una oferta activa para este espacio.")

    entry = repo.get_waitlist_entry(entry_id)
    if entry is None or entry["status"] != "activa":
        raise WaitlistError("El paciente no está activo en la lista de espera.")
    patient = repo.get_patient(entry["phone"])
    if patient is None or not patient["has_consent"] or patient["opted_out"]:
        raise WaitlistError("El paciente no tiene consentimiento o pidió la baja.")
    if repo.get_active_offer_for_entry(entry_id) is not None:
        raise WaitlistError("El paciente ya tiene una oferta activa.")
    since = now - timedelta(days=7)
    if repo.count_offers_for_entry_since(entry_id, since) >= max_offers_per_week:
        raise WaitlistError("El paciente alcanzó el máximo de ofertas por semana.")

    starts_at = datetime.fromisoformat(slot["starts_at"])
    ends_at = datetime.fromisoformat(slot["ends_at"])
    if starts_at <= now:
        raise WaitlistError("El espacio ya empezó.")
    if repo.has_appointment_at(starts_at):
        repo.set_freed_slot_status(slot_id, "ocupado")
        raise WaitlistError("El espacio ya fue ocupado por otra cita.")
    if repo.has_appointment_for_phone_at(entry["phone"], starts_at):
        raise WaitlistError("El paciente ya tiene una cita en ese horario.")

    ttl = (
        NEAR_SLOT_TTL_MINUTES
        if starts_at - now < timedelta(hours=NEAR_SLOT_HOURS)
        else DEFAULT_TTL_MINUTES
    )
    expires_at = min(now + timedelta(minutes=ttl), starts_at)
    if expires_at <= now:
        raise WaitlistError("El espacio es demasiado inminente para ofrecerlo.")

    offer_id = repo.create_slot_offer(
        freed_slot_id=slot_id,
        waitlist_entry_id=entry_id,
        sent_at=now,
        expires_at=expires_at,
    )
    repo.set_freed_slot_status(slot_id, "ofrecido")
    repo.mark_waitlist_offered(entry_id, now)

    try:
        messaging.send(
            entry["phone"],
            format_slot_offer(entry["patient_name"], starts_at, ends_at, clinic_tz),
        )
    except Exception as exc:  # no dejar una oferta fantasma si el envío falla
        repo.update_slot_offer(
            offer_id, status="cancelada", response="fallo_envio", responded_at=now
        )
        repo.set_freed_slot_status(slot_id, "libre")
        raise WaitlistError("No se pudo enviar la oferta.") from exc

    return repo.get_slot_offer(offer_id) or {}


def respond_offer(
    repo: Repository,
    messaging: MessagingPort,
    *,
    offer_id: int,
    action: str,
    now: datetime,
    clinic_tz: tzinfo,
) -> dict:
    """Aplica aceptar o rechazar a una oferta enviada."""
    if action not in {"aceptar", "rechazar"}:
        raise WaitlistError("Respuesta inválida.")

    offer = repo.get_slot_offer(offer_id)
    if offer is None or offer["status"] != "enviada":
        raise WaitlistError("La oferta ya no está activa.")
    if datetime.fromisoformat(offer["expires_at"]) <= now:
        repo.update_slot_offer(offer_id, status="vencida", responded_at=now)
        repo.set_freed_slot_status(offer["freed_slot_id"], "libre")
        raise WaitlistError("La oferta venció.")

    entry = repo.get_waitlist_entry(offer["waitlist_entry_id"])
    if entry is None:
        raise WaitlistError("No encontramos el paciente de la oferta.")
    patient = repo.get_patient(entry["phone"])
    can_message = bool(
        patient is not None and patient["has_consent"] and not patient["opted_out"]
    )

    slot = repo.get_freed_slot(offer["freed_slot_id"])
    if action == "aceptar":
        if slot is not None and repo.has_appointment_at(
            datetime.fromisoformat(slot["starts_at"])
        ):
            repo.update_slot_offer(
                offer_id, status="cancelada", response="ocupado", responded_at=now
            )
            repo.set_freed_slot_status(slot["id"], "ocupado")
            raise WaitlistError("El espacio ya fue ocupado.")
        repo.update_slot_offer(
            offer_id, status="aceptada", response="aceptada", responded_at=now
        )
        if slot is not None:
            repo.set_freed_slot_status(slot["id"], "reservado_pendiente")
        if can_message:
            try:
                messaging.send(entry["phone"], SLOT_ACCEPTED)
            except Exception:
                pass
    else:
        repo.update_slot_offer(
            offer_id, status="rechazada", response="rechazada", responded_at=now
        )
        if slot is not None:
            repo.set_freed_slot_status(slot["id"], "libre")
        if can_message:
            try:
                messaging.send(entry["phone"], SLOT_DECLINED)
            except Exception:
                pass

    return repo.get_slot_offer(offer_id) or {}


def expire_offers(repo: Repository, *, now: datetime) -> int:
    """Vence las ofertas cuyo plazo pasó y libera el espacio."""
    expired = 0
    for offer in repo.list_sent_offers():
        if datetime.fromisoformat(offer["expires_at"]) > now:
            continue
        repo.update_slot_offer(offer["id"], status="vencida", responded_at=now)
        slot = repo.get_freed_slot(offer["freed_slot_id"])
        if slot is not None and slot["status"] == "ofrecido":
            repo.set_freed_slot_status(slot["id"], "libre")
        expired += 1
    return expired


def confirm_recovered(repo: Repository, *, slot_id: int, now: datetime) -> None:
    """La asistente confirma que movió o creó la cita en Google Calendar."""
    slot = repo.get_freed_slot(slot_id)
    if slot is None:
        raise WaitlistError("No encontramos el espacio.")
    if slot["status"] != "reservado_pendiente":
        raise WaitlistError("El espacio no está reservado pendiente.")
    repo.set_freed_slot_status(slot_id, "recuperado", recovered_at=now)


def close_slot(repo: Repository, *, slot_id: int, now: datetime) -> None:
    """Cierra un espacio como no recuperado y cancela su oferta activa."""
    slot = repo.get_freed_slot(slot_id)
    if slot is None:
        raise WaitlistError("No encontramos el espacio.")
    active = repo.get_active_offer_for_slot(slot_id)
    if active is not None:
        repo.update_slot_offer(active["id"], status="cancelada", responded_at=now)
    repo.set_freed_slot_status(slot_id, "no_recuperado")
