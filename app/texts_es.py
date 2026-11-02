"""Textos en español para pacientes y panel (constitución 12)."""

from __future__ import annotations

from datetime import date, datetime, tzinfo

DIAS_SEMANA = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]
MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def fecha_larga(d: date) -> str:
    """Fecha en español: «Lunes 3 de noviembre»."""
    return f"{DIAS_SEMANA[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]}"


def format_reminder(
    kind: str, patient_name: str, starts_at: datetime, clinic_tz: tzinfo
) -> str:
    """Cuerpo del recordatorio según la spec 4.3 (R1, R2 o inmediato)."""
    local = starts_at.astimezone(clinic_tz)
    dia = DIAS_SEMANA[local.weekday()]
    fecha = f"{local.day} de {MESES[local.month - 1]}"
    hora = local.strftime("%H:%M")
    if kind == "R2":
        return (
            f"Hola {patient_name}, tu cita en el consultorio de la Dra. Laura "
            f"es mañana, {dia} {fecha} a las {hora}. ¿Sigues pudiendo asistir?"
        )
    return (
        f"Hola {patient_name}, te recordamos tu cita en el consultorio de la "
        f"Dra. Laura el {dia} {fecha} a las {hora}. ¿Nos confirmas?"
    )


def format_slot_offer(
    patient_name: str,
    starts_at: datetime,
    ends_at: datetime,
    clinic_tz: tzinfo,
) -> str:
    """Mensaje de oferta de un espacio liberado."""
    local = starts_at.astimezone(clinic_tz)
    local_end = ends_at.astimezone(clinic_tz)
    dia = DIAS_SEMANA[local.weekday()]
    fecha = f"{local.day} de {MESES[local.month - 1]}"
    return (
        f"Hola {patient_name}, se liberó un espacio el {dia} {fecha} de "
        f"{local.strftime('%H:%M')} a {local_end.strftime('%H:%M')}. "
        "¿Lo tomas? Responde «Lo tomo» o «No puedo»."
    )


AUTO_REPLY = {
    "confirm": "¡Gracias! Te esperamos.",
    "reschedule": "Entendido. La asistente te contactará para elegir una nueva fecha.",
    "cancel": "Listo, cancelamos tu cita. Si quieres agendar otra, escríbenos.",
}

SLOT_ACCEPTED = "¡Listo! La asistente te confirmará la cita."
SLOT_DECLINED = "Gracias, te avisaremos si surge otro espacio."

# Nombres en español de los estados (spec 4.2).
STATE_LABELS = {
    "pending": "Pendiente",
    "reminder_sent": "Recordatorio enviado",
    "confirmed": "Confirmada",
    "reschedule_requested": "Reprogramación solicitada",
    "cancelled_by_patient": "Cancelada por paciente",
    "unconfirmed": "Sin confirmar",
    "send_error": "Error de envío",
    "no_consent": "Sin consentimiento",
    "no_phone": "Sin teléfono",
}

# Textos del panel.
ATTENTION_TITLE = "Requieren atención"
AGENDA_TITLE = "Agenda"
EMPTY_STATE = "Hoy no hay citas."
