"""Textos en español para pacientes y panel (constitución 12)."""

from __future__ import annotations

AUTO_REPLY = {
    "confirm": "¡Gracias! Te esperamos.",
    "reschedule": "Entendido. La asistente te contactará para elegir una nueva fecha.",
    "cancel": "Listo, cancelamos tu cita. Si quieres agendar otra, escríbenos.",
}

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
