# Plan técnico — Spec 003

**Feature:** Recuperación de espacios liberados con lista de espera.
**Base:** [spec.md](spec.md). **Estado:** fases 1–5 implementadas en modo demo; pendiente el modo real y el piloto.

## 1. Enfoque

La app **no escribe en Google Calendar**. Detecta espacios que ya quedaron libres, los ofrece por WhatsApp a pacientes de una lista de espera y le pide a la asistente que mueva la cita en Calendar. La asistente confirma en la app; así se evita la doble reserva y se respeta la fuente de verdad.

Principios:

- Una sola oferta activa por espacio.
- Un solo candidato a la vez.
- Revalidar contra Calendar antes de ofrecer y antes de confirmar.
- Sin datos clínicos: solo tipo de cita general y preferencias.
- Todo medido con eventos y línea base.

## 2. Modelo de datos (schema v2)

| Tabla / campo | Campos | Para qué |
|---|---|---|
| appointments.ends_at | ends_at | Duración del espacio que se libera |
| waitlist_entries | id, patient_name, phone, reason, preferred_days, preferred_time_start, preferred_time_end, source, created_at, status, last_offered_at | Pacientes que aceptan venir antes; source='asistente' en MVP |
| freed_slots | id, event_id, starts_at, ends_at, duration_estimated, source (cancelled/rescheduled), created_at, status | Espacio que quedó libre |
| slot_offers | id, freed_slot_id, waitlist_entry_id, sent_at, expires_at, responded_at, response, status | Oferta y respuesta |
| patients | ya existe: phone, has_consent, opted_out | Consentimiento y baja |

Reglas:

- Un espacio tiene máximo una oferta con estado `enviada` (índice único parcial o validación en repositorio).
- Un paciente tiene máximo una oferta activa y 2 ofertas por semana por defecto (tope 3).
- `preferred_days` se guarda como máscara de 7 bits o JSON; `preferred_time_start/end` como horas.
- `reason` solo admite valores generales: consulta, limpieza, control, tratamiento.
- `ends_at` se toma del evento de Google Calendar. Si no viene, se usa una duración configurable (por defecto 30 min) y se marca como supuesto.

## 3. Detección del espacio

En `sync_calendar`:

1. Si una cita existente desaparece del calendario, antes de borrarla se crea un `freed_slot` con sus datos.
2. Si cambia de fecha/hora, se crea un `freed_slot` con la fecha anterior y se actualiza la cita.
3. Si la cita sigue en el calendario, no se libera nada: la asistente debe moverla o eliminarla primero.
4. El estado `cancelled_by_patient` en la app **no** libera el espacio por sí solo; solo lo hace el cambio real en Calendar.

Esto evita ofrecer un espacio que todavía está ocupado.

## 4. Matching y ranking

Filtros:

- `waitlist_entries.status = activa`.
- Paciente con consentimiento y sin baja.
- Sin oferta activa.
- Sin otra cita en el mismo horario.
- Preferencia de día/hora compatible, si existe.

Puntaje simple:

| Señal | Puntos |
|---|---|
| Coincide el día preferido | +3 |
| Coincide la franja horaria | +2 |
| Lleva más días esperando | +1 por semana, tope +3 |
| Tipo de cita general | Solo se muestra; no puntúa en el MVP |

Se muestran los 3 mejores con el motivo: «prefiere los miércoles», «prefiere la tarde», «espera desde hace 12 días».

No se usa puntaje clínico ni diagnósticos.

## 5. Ciclo de la oferta

```
freed_slot (libre)
  -> oferta enviada (un candidato, vence a los 30 min)
  -> aceptada -> reservado_pendiente -> asistente confirma -> recuperado
  -> rechazada / vencida -> siguiente candidato
  -> sin candidatos -> no_recuperado
```

Reglas:

- Antes de enviar: revalidar que el espacio sigue libre y que el paciente sigue elegible. El candidato muestra si ya tiene una cita futura (para moverla) o si habrá que crearla.
- La oferta respeta la ventana 8:00–20:00; si el espacio es inminente y la ventana está cerrada, no se envía y la asistente ve el aviso.
- Vencimiento: 30 min por defecto; 15 min si el espacio es en menos de 2 h; configurable entre 10 y 120.
- Si el paciente acepta: se marcan `reservado_pendiente`, se cierra la oferta y se crea una tarea para la asistente.
- Si el espacio se ocupa antes de confirmar: se cancela la oferta y se avisa; no se crea una segunda reserva.
- Al confirmar la asistente: `recuperado`; se guarda el tiempo de llenado.

## 6. Rutas y UI

| Ruta | Función |
|---|---|
| GET /lista-espera | Lista de pacientes, estado, preferencias y última oferta |
| POST /lista-espera/crear | Registrar paciente (nombre, teléfono, tipo general, preferencias, consentimiento) |
| POST /lista-espera/editar | Editar, pausar o retirar |
| GET /espacios/{id} | Detalle del espacio liberado y candidatos |
| POST /espacios/{id}/ofrecer | Enviar oferta al candidato elegido |
| POST /espacios/{id}/confirmar | La asistente confirma que movió la cita en Calendar |
| POST /espacios/{id}/cerrar | Cerrar como no recuperado o cancelar |
| POST /sim/lista-espera/* | Crear, aceptar, rechazar, vencer y restaurar en demo |

UI:

- **Panel:** los espacios liberados aparecen en «Requieren atención» con fecha, hora, duración y acción **Ofrecer a lista de espera**.
- **Lista de espera:** tabla/lista con nombre, teléfono, preferencia, estado y última oferta. Alta y edición en formulario simple.
- **Detalle del espacio:** candidatos con motivo del match, vista previa del mensaje, temporizador de vencimiento y estado.
- **Tarea de la asistente:** «Mueve la cita en Google Calendar y confirma aquí»; nunca se cierra sola.
- **Móvil:** filas, no tarjetas; 44 px; sin cortes de texto.

## 7. Puertos y adaptadores

- **CalendarPort:** añadir `ends_at` a `CalendarEvent`; Google Calendar lo lee de `end.dateTime`. Sigue siendo solo lectura.
- **MessagingPort:** nueva plantilla `slot_available` con dos botones («Lo tomo», «No puedo»). El cuerpo no incluye datos clínicos.
- **ClockPort:** vencimiento de la oferta y ventana de envío.
- **FakeCalendar / SimulatedMessaging:** permitir crear espacios, aceptar, rechazar, vencer y restaurar.

## 8. Pruebas

- **Dominio:** ranking, filtros, estados de la oferta, vencimiento, una oferta activa por espacio y por paciente.
- **Sincronización:** cancelación y reprogramación crean el espacio con duración; una cita que sigue en Calendar no lo crea.
- **Ofertas:** consentimiento, baja, ventana, revalidación, no duplicados.
- **Web:** panel, lista de espera, detalle, confirmación, modo demo y 360 px.
- **Aceptación:** CA-1 a CA-8 de la spec.
- **Métricas:** eventos emitidos en cada transición y cálculo de la tasa de recuperación.
- **Ninguna prueba llama a Google ni a WhatsApp reales.**

## 9. Instrumentación

Eventos:

- `espacio_liberado`
- `oferta_enviada`
- `oferta_aceptada`
- `oferta_rechazada`
- `oferta_vencida`
- `espacio_recuperado`
- `espacio_no_recuperado`
- `baja_paciente`

En el MVP demo, la tasa se calcula de freed_slots y slot_offers. El log de eventos y el tablero semanal quedan para el piloto.

Tablero semanal:

- Espacios liberados, ofrecidos, recuperados.
- Tasa de recuperación y tiempo medio de llenado.
- Respuesta en 1 h y ofertas vencidas.
- Dobles reservas y bajas.
- Tiempo manual de la asistente.
- Ingreso recuperado con el valor medio de cita del consultorio.

## 10. Plan de implementación

| Fase | Entregable | Criterio de salida |
|---|---|---|
| 1. Datos y detección | Schema v2, ends_at, freed_slots, sync | Cancelar/mover en demo crea el espacio correcto |
| 2. Lista de espera y matching | Tabla, alta/edición, ranking | CA-1 y CA-3 con candidatos ordenados |
| 3. Oferta y respuesta | Envío, vencimiento, aceptar/rechazar | CA-3, CA-4, CA-5, CA-7 |
| 4. Confirmación y panel | Tarea de asistente, recuperado, panel | CA-2, CA-6, CA-8 |
| 5. Métricas y demo | Resumen de recuperación, simulador y demo | Tasa calculada desde las tablas; demo restaurable |

## 11. Plan de piloto

- **Antes:** 4 semanas de línea base por consultorio (espacios liberados, llenados, no-show, tiempo de la asistente).
- **Piloto:** 3–5 consultorios del ICP, 4 semanas, con la función activada.
- **Semana 1:** onboarding y prueba con datos ficticios.
- **Semana 2–4:** uso real; revisión semanal de ofertas, respuestas y dobles reservas.
- **Criterios para seguir:** recuperar ≥20 % de espacios a 30 días, 0 dobles reservas, <2 % de bajas, y la asistente completa el flujo en <2 min.
- **Criterios para corregir:** si la respuesta es baja, ajustar ventana, texto o preferencias; si hay fatiga, bajar el máximo de ofertas; si no hay lista, trabajar el onboarding.

## 12. Riesgos técnicos

| Riesgo | Mitigación |
|---|---|
| Espacio ocupado antes de responder | Revalidar Calendar antes de enviar y antes de confirmar |
| Duración desconocida | ends_at del evento o duración configurable |
| Carrera entre dos ofertas | Índice único de oferta activa por espacio; transacción |
| Oferta enviada fuera de ventana | Validar ClockPort antes de enviar |
| Paciente sin consentimiento | Filtro duro y estado visible |
| Plantilla no aprobada | Verificar en documentación oficial antes del piloto |
| Fatiga de ofertas | Máximo 3 por semana y baja fácil |
| La asistente no confirma | Tarea visible; el espacio no se cierra solo |

## 13. Decisiones tomadas y pendientes

**Tomadas para el MVP:**

1. Duración desde `ends_at` con fallback de 30 min y marca de estimada.
2. Vencimiento de 30 min (15 min si faltan <2 h), configurable entre 10 y 120.
3. Máximo de 2 ofertas por semana por paciente, con tope duro de 3.
4. Lista de espera creada solo por la asistente; `source='asistente'` en el MVP.

**Pendientes:**

1. ¿Cómo se obtiene y registra el consentimiento en el consultorio?
2. ¿Se permite una excepción de ventana para espacios inminentes o se llama al paciente?

## 14. Fuera de alcance técnico

- Escribir en Google Calendar.
- Reasignación automática sin asistente.
- Priorización clínica.
- Historia clínica o datos de salud.
- SMS, correo o llamadas.
- Multisede y lista pública.
