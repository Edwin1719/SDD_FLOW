"""Tests de la lista de espera y recuperación de espacios (Spec 002)."""

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.sim_messaging import SimulatedMessaging
from app.db.repository import connect
from app.services.waitlist import (
    WaitlistError,
    candidates,
    confirm_recovered,
    expire_offers,
    respond_offer,
    send_offer,
)

UTC = timezone.utc
NOW = datetime(2026, 11, 2, 10, 0, tzinfo=UTC)  # lunes 10:00
SLOT_START = datetime(2026, 11, 2, 15, 0, tzinfo=UTC)
SLOT_END = datetime(2026, 11, 2, 15, 30, tzinfo=UTC)
PHONE = "+573004567890"


def _entry(
    repo,
    *,
    name="Carla",
    phone=PHONE,
    consent=True,
    opted_out=False,
    status="activa",
    days="0,2,4",
):
    repo.upsert_patient(phone, has_consent=consent, opted_out=opted_out)
    return repo.create_waitlist_entry(
        patient_name=name,
        phone=phone,
        reason="limpieza",
        preferred_days=days,
        preferred_time_start="14:00",
        preferred_time_end="18:00",
        status=status,
        created_at=NOW - timedelta(days=8),
    )


def _slot(repo, starts_at=SLOT_START, ends_at=SLOT_END, event_id="evt-old"):
    return repo.create_freed_slot(
        event_id=event_id,
        starts_at=starts_at,
        ends_at=ends_at,
        duration_estimated=False,
        source="cancelada",
        created_at=NOW,
    )


def test_candidates_only_eligible(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    active = _entry(repo, name="Activa")
    _entry(repo, name="Sin consentimiento", phone="+573001111111", consent=False)
    _entry(repo, name="Pausada", phone="+573002222222", status="pausada")
    _entry(repo, name="Baja", phone="+573003333333", opted_out=True)
    slot = repo.get_freed_slot(_slot(repo))

    result = candidates(repo, slot, now=NOW, clinic_tz=UTC)

    assert [item["id"] for item in result] == [active]
    repo.close()


def test_send_offer_outside_window_fails(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))

    with pytest.raises(WaitlistError, match="ventana"):
        send_offer(
            repo,
            SimulatedMessaging(),
            slot_id=slot["id"],
            entry_id=entry,
            now=datetime(2026, 11, 2, 21, 0, tzinfo=UTC),
            clinic_tz=UTC,
        )
    repo.close()


def test_send_offer_and_one_active(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))

    offer = send_offer(
        repo,
        messaging,
        slot_id=slot["id"],
        entry_id=entry,
        now=NOW,
        clinic_tz=UTC,
    )

    assert offer["status"] == "enviada"
    assert repo.get_freed_slot(slot["id"])["status"] == "ofrecido"
    assert "se liberó un espacio" in messaging.messages[0][1]
    with pytest.raises(WaitlistError, match="no está libre"):
        send_offer(
            repo,
            messaging,
            slot_id=slot["id"],
            entry_id=entry,
            now=NOW,
            clinic_tz=UTC,
        )
    repo.close()


def test_accept_and_confirm_recovers(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))
    offer = send_offer(
        repo, messaging, slot_id=slot["id"], entry_id=entry, now=NOW, clinic_tz=UTC
    )

    accepted = respond_offer(
        repo,
        messaging,
        offer_id=offer["id"],
        action="aceptar",
        now=NOW,
        clinic_tz=UTC,
    )

    assert accepted["status"] == "aceptada"
    assert repo.get_freed_slot(slot["id"])["status"] == "reservado_pendiente"
    assert any("La asistente te confirmará" in body for _, body in messaging.messages)

    confirm_recovered(repo, slot_id=slot["id"], now=NOW + timedelta(minutes=5))
    assert repo.get_freed_slot(slot["id"])["status"] == "recuperado"
    repo.close()


def test_decline_frees_slot(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))
    offer = send_offer(
        repo, messaging, slot_id=slot["id"], entry_id=entry, now=NOW, clinic_tz=UTC
    )

    respond_offer(
        repo,
        messaging,
        offer_id=offer["id"],
        action="rechazar",
        now=NOW,
        clinic_tz=UTC,
    )

    assert repo.get_freed_slot(slot["id"])["status"] == "libre"
    assert repo.get_slot_offer(offer["id"])["status"] == "rechazada"
    repo.close()


def test_expire_offer(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))
    offer = send_offer(
        repo, messaging, slot_id=slot["id"], entry_id=entry, now=NOW, clinic_tz=UTC
    )

    expired = expire_offers(repo, now=NOW + timedelta(minutes=31))

    assert expired == 1
    assert repo.get_freed_slot(slot["id"])["status"] == "libre"
    assert repo.get_slot_offer(offer["id"])["status"] == "vencida"
    repo.close()


def test_max_two_offers_per_week(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    messaging = SimulatedMessaging()
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))

    first = send_offer(
        repo, messaging, slot_id=slot["id"], entry_id=entry, now=NOW, clinic_tz=UTC
    )
    respond_offer(
        repo, messaging, offer_id=first["id"], action="rechazar", now=NOW, clinic_tz=UTC
    )
    second = send_offer(
        repo, messaging, slot_id=slot["id"], entry_id=entry, now=NOW, clinic_tz=UTC
    )
    respond_offer(
        repo,
        messaging,
        offer_id=second["id"],
        action="rechazar",
        now=NOW,
        clinic_tz=UTC,
    )

    with pytest.raises(WaitlistError, match="máximo"):
        send_offer(
            repo,
            messaging,
            slot_id=slot["id"],
            entry_id=entry,
            now=NOW,
            clinic_tz=UTC,
        )
    repo.close()


def test_slot_occupied_by_appointment(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    entry = _entry(repo)
    slot = repo.get_freed_slot(_slot(repo))
    repo.create_appointment(
        event_id="evt-new",
        patient_name="Otro",
        phone="+573009999999",
        starts_at=SLOT_START,
        ends_at=SLOT_END,
        status="pending",
        updated_at=NOW,
    )

    with pytest.raises(WaitlistError, match="ocupado"):
        send_offer(
            repo,
            SimulatedMessaging(),
            slot_id=slot["id"],
            entry_id=entry,
            now=NOW,
            clinic_tz=UTC,
        )
    assert repo.get_freed_slot(slot["id"])["status"] == "ocupado"
    repo.close()


def test_no_consent_is_not_candidate(tmp_path):
    repo = connect(tmp_path / "data" / "db.sqlite")
    _entry(repo, consent=False)
    slot = repo.get_freed_slot(_slot(repo))

    assert candidates(repo, slot, now=NOW, clinic_tz=UTC) == []
    repo.close()
