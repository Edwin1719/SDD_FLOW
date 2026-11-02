# Tareas — Spec 002

Implementación por fases. Todas las fases quedaron en verde en modo demo.

- [x] T1. Datos y detección: schema v2, `ends_at`, `waitlist_entries`, `freed_slots`, `slot_offers`, migración desde v1; sincronización que crea el espacio al cancelar o mover. (RF-4, RF-5, RF-6)
      Hecho cuando: cancelar o mover una cita en demo crea el espacio con hora y duración, y una cita sigue ocupada si el evento permanece en Calendar.

- [x] T2. Lista de espera: alta con nombre, teléfono, tipo de cita general, preferencias, consentimiento y origen; pausar, reactivar y retirar; matching por día, franja y antigüedad. (RF-1, RF-2, RF-3, RF-7)
      Hecho cuando: los pacientes sin consentimiento o de baja no son candidatos; los activos aparecen ordenados.

- [x] T3. Oferta: envío a un candidato, una sola oferta activa por espacio, vencimiento de 30 min (15 min si faltan <2 h), ventana 8:00–20:00 y máximo de 2 ofertas por semana (tope 3). (RF-8, RF-9, RF-10)
      Hecho cuando: no se envía fuera de ventana, sin consentimiento o con una oferta activa; el mensaje incluye fecha y hora.

- [x] T4. Respuesta y cierre: aceptar, rechazar, vencer, reservar pendiente, confirmar recuperado y cerrar como no recuperado; sin doble reserva. (RF-11, RF-12, RF-13, RF-14, RF-15)
      Hecho cuando: aceptar reserva el espacio, rechazar o vencer lo libera y confirmar lo marca recuperado.

- [x] T5. Web y demo: panel con espacios liberados, página de lista de espera, detalle del espacio, respuestas desde el simulador y seed con pacientes de espera. (RF-16, RF-17, RF-18)
      Hecho cuando: el flujo se recorre a 360 px, no hay datos clínicos y la demo se restaura.

- [x] T6. Pruebas: servicio de lista de espera, sincronización, web y aceptación; actualización del esquema. (CA-1 a CA-8)
      Hecho cuando: `pytest -q` pasa completo y `ruff check` no reporta errores. Resultado: **117 pruebas en verde**.

- [x] T7. Documentación: spec, plan, tareas y README actualizados con la feature y sus límites.
