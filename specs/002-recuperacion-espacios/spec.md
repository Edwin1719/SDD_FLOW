# Spec 002 — Recuperación de espacios liberados

**Proyecto:** Recordatorios para consultorio dental
**Estado:** implementada en modo demo. Pendiente el modo real y el piloto.
**Fecha:** 2026-11-02
**Base:** [Spec 001](../001-recordatorios-confirmacion/spec.md) y [ICP del proyecto](../../ICP.md).

## 1. Contexto y problema

La app ya reduce inasistencias con recordatorios y confirmación de un toque. Pero cuando un paciente cancela o reprograma, el espacio queda libre y el consultorio pierde la silla. La asistente lo ve en «Requieren atención», pero llenarlo depende de llamar o escribir a pacientes uno por uno, y casi nunca se logra a tiempo.

**La mitad que falta:** convertir un espacio liberado en una cita recuperada, sin que la asistente persiga pacientes y sin que la app escriba en Google Calendar.

## 2. Objetivo

Permitir que la asistente **ofrezca un espacio liberado a pacientes de una lista de espera**, reciba una respuesta de un toque y confirme la recuperación después de mover la cita en Google Calendar.

La característica debe **funcionar** (flujo corto, sin dobles reservas, sin datos clínicos) e **importar** (recuperar espacios y demostrar el retorno con métricas).

## 3. Usuarios e historias

- **Asistente (usuaria principal):** quiere llenar el espacio en menos de 2 minutos, sin llamar a diez pacientes.
- **Paciente en lista de espera:** quiere una cita antes si se libera un espacio; responde con un toque.
- **Dra. Laura (dueña):** quiere ver cuántos espacios se recuperaron y cuánto tiempo se ahorró.

**Historias:**

- **H1:** Como asistente quiero registrar pacientes que aceptan venir antes, para tener a quién ofrecerle un espacio.
- **H2:** Como asistente quiero que, al liberarse un espacio, la app me muestre los mejores candidatos, para no buscarlos a mano.
- **H3:** Como paciente quiero recibir un WhatsApp con el espacio y responder «Lo tomo» o «No puedo», para decidir en segundos.
- **H4:** Como asistente quiero confirmar que moví la cita en Google Calendar, para cerrar el espacio y evitar dobles reservas.
- **H5:** Como dueña quiero ver espacios recuperados, tiempo de llenado y aceptación, para saber si la función importa.

## 4. Flujo

1. La asistente registra un paciente en la **lista de espera** (nombre, teléfono, tipo de cita general, días y horarios preferidos, consentimiento).
2. El paciente cancela o se reprograma; la asistente **libera el espacio en Google Calendar** (la app no lo hace).
3. La sincronización detecta que el espacio quedó libre y crea una **oferta de espacio**.
4. La app propone hasta 3 candidatos compatibles y la asistente elige uno.
5. Se envía un WhatsApp con el espacio y dos botones: **Lo tomo** / **No puedo**.
6. Si acepta, el espacio queda **reservado pendiente**; la asistente mueve la cita en Google Calendar y marca **Recuperado**.
7. Si rechaza o expira, se ofrece al siguiente candidato. Si nadie acepta, el espacio se cierra como **No recuperado**.

## 5. Alcance

**Dentro:**

- Lista de espera con datos mínimos y consentimiento.
- Detección de espacios liberados por cancelación o reprogramación en Google Calendar.
- Ranking simple de candidatos por preferencia y antigüedad.
- Oferta por WhatsApp, un candidato a la vez, con expiración.
- Respuesta de un toque y confirmación de la asistente.
- Historial y métricas de recuperación.
- Modo demo con pacientes, espacios y respuestas simuladas.

**Fuera:**

- Escribir o mover citas en Google Calendar.
- Reasignación automática sin intervención de la asistente.
- Subastas, priorización clínica o triaje.
- Historia clínica, diagnósticos, odontograma o imágenes.
- SMS, correo o llamadas automáticas.
- Múltiples sedes, lista de espera pública o autoservicio del paciente.

## 6. Requisitos funcionales (EARS)

### Lista de espera

- **RF-1:** EL SISTEMA permitirá a la asistente registrar un paciente en la lista de espera con nombre, teléfono, tipo de cita en términos generales, días y horarios preferidos, consentimiento y origen de la entrada. En esta versión solo la asistente crea entradas; el campo `source` queda preparado para un futuro autoservicio.
- **RF-2:** EL SISTEMA solo incluirá en las ofertas a pacientes con consentimiento y sin baja; los demás quedarán visibles como «Sin consentimiento» o «Baja».
- **RF-3:** EL SISTEMA permitirá editar, pausar y retirar una entrada de la lista de espera.

### Detección del espacio

- **RF-4:** CUANDO una cita desaparezca o cambie de fecha u hora en Google Calendar, EL SISTEMA creará un espacio liberado con la fecha, hora y duración originales. La duración sale del `ends_at` del evento; si no existe, se usa la duración por defecto del consultorio (30 min) y se marca como estimada.
- **RF-5:** EL SISTEMA mostrará el espacio liberado en «Requieren atención» con la acción **Ofrecer a lista de espera**.
- **RF-6:** EL SISTEMA no ofrecerá un espacio que siga ocupado en Google Calendar; si el calendario cambia antes de enviar la oferta, la cancelará.

### Oferta

- **RF-7:** CUANDO la asistente pida ofrecer un espacio, EL SISTEMA mostrará hasta 3 candidatos ordenados por coincidencia de preferencias y tiempo de espera, con el motivo del match.
- **RF-8:** EL SISTEMA enviará la oferta a un solo candidato a la vez, dentro de la ventana de envío de 8:00 a 20:00, con un vencimiento por defecto de 30 minutos (15 minutos si faltan menos de 2 h para el espacio) y configurable entre 10 y 120 minutos.
- **RF-9:** EL SISTEMA no enviará la oferta si el paciente no tiene consentimiento, pidió la baja, ya tiene una oferta activa o superó el máximo de ofertas por semana (2 por defecto, tope 3).
- **RF-10:** EL SISTEMA no enviará dos ofertas activas para el mismo espacio ni el mismo recordatorio dos veces.

### Respuesta y cierre

- **RF-11:** CUANDO el paciente pulse «Lo tomo», EL SISTEMA marcará el espacio como **Reservado pendiente** y mostrará a la asistente qué hacer en Google Calendar: mover la cita existente del paciente o crear una nueva, sin escribir en el calendario.
- **RF-12:** CUANDO el paciente pulse «No puedo» o la oferta venza, EL SISTEMA cerrará esa oferta y permitirá ofrecer el espacio al siguiente candidato.
- **RF-13:** CUANDO la asistente confirme que movió la cita en Google Calendar, EL SISTEMA marcará el espacio como **Recuperado** y cerrará la oferta.
- **RF-14:** SI el espacio deja de estar libre antes de que la asistente confirme, ENTONCES EL SISTEMA cancelará la oferta y avisará a la asistente; nunca habrá dos pacientes confirmados para el mismo espacio.
- **RF-15:** EL SISTEMA guardará el historial de espacios liberados, ofertas, respuestas y resultado para medir la recuperación.

### Privacidad y demo

- **RF-16:** EL SISTEMA solo guardará datos mínimos: nombre, teléfono, tipo de cita general, preferencias, consentimiento y estado. Nunca diagnósticos ni notas clínicas.
- **RF-17:** EL SISTEMA respetará la baja del paciente y no le enviará más ofertas.
- **RF-18:** EL MODO DEMO permitirá crear espacios, pacientes en espera, aceptar, rechazar, dejar vencer y restaurar datos sin credenciales.

## 7. Estados

**Entrada de lista de espera:** activa, pausada, retirada, sin_consentimiento, baja.

**Espacio liberado:** libre, ofrecido, reservado_pendiente, recuperado, no_recuperado.

**Oferta:** enviada, aceptada, rechazada, vencida, cancelada.

Reglas:

- Un espacio tiene **una sola oferta activa**.
- Un paciente tiene **una sola oferta activa** y un máximo de **2 ofertas por semana** por defecto, con **tope duro de 3**.
- La oferta vence a los **30 minutos** por defecto, o a los **15 minutos** si el espacio es en menos de 2 h.
- La asistente siempre confirma el movimiento en Google Calendar; la app no escribe en el calendario.

## 8. Criterios de aceptación

**CA-1 — Lista de espera (RF-1, RF-2, RF-3)**
- Dado un paciente con consentimiento, cuando la asistente lo registra con sus preferencias, entonces aparece como activo y es elegible para ofertas. Sin consentimiento, no es elegible y se muestra como «Sin consentimiento».

**CA-2 — Detección del espacio (RF-4, RF-5, RF-6)**
- Dado una cita cancelada o movida en Google Calendar, cuando corre la sincronización, entonces el espacio aparece en «Requieren atención» con fecha, hora y duración, y solo si ya está libre.

**CA-3 — Oferta al candidato correcto (RF-7, RF-8, RF-9, RF-10)**
- Dado un espacio libre y varios candidatos, cuando la asistente pide ofrecerlo, entonces ve hasta 3 candidatos ordenados y se envía una sola oferta al elegido, dentro de la ventana y con consentimiento.

**CA-4 — Aceptación de un toque (RF-11)**
- Dado una oferta enviada, cuando el paciente pulsa «Lo tomo», entonces el espacio pasa a «Reservado pendiente», la asistente ve la tarea (mover la cita existente o crear una nueva) y no se envían más ofertas para ese espacio.

**CA-5 — Rechazo o expiración (RF-12)**
- Dado una oferta rechazada o vencida, cuando se cierra, entonces el espacio puede ofrecerse al siguiente candidato y el historial registra la respuesta.

**CA-6 — Confirmación de recuperación (RF-13, RF-14)**
- Dado un espacio reservado, cuando la asistente confirma que movió la cita en Google Calendar, entonces el espacio pasa a «Recuperado» y desaparece de «Requieren atención». Si el espacio se ocupó antes, la oferta se cancela y no hay doble reserva.

**CA-7 — Consentimiento y baja (RF-2, RF-9, RF-17)**
- Dado un paciente sin consentimiento o con baja, cuando se intenta ofrecer un espacio, entonces no se envía ningún mensaje y la app explica por qué.

**CA-8 — Uso en celular y privacidad (RF-16, RF-18)**
- Dado el panel y la lista de espera a 360 px, cuando se recorre el flujo, entonces no hay cortes de texto, las acciones son de 44 px, no se muestran datos clínicos y la demo se puede restaurar.

## 9. Métricas de éxito

### Norte

**Tasa de recuperación de espacios liberados** = espacios recuperados en 24 h / espacios liberados.

Es la métrica que dice si la función **importa**. Debe medirse contra una línea base de 4 semanas antes del piloto.

### Funciona (producto)

| Métrica | Qué responde | Objetivo inicial |
|---|---|---|
| Tiempo hasta la primera oferta | ¿La asistente puede actuar rápido? | < 10 min desde que se libera |
| Tiempo de la asistente por espacio | ¿El flujo es corto? | < 2 min |
| Tasa de entrega de la oferta | ¿El mensaje sale? | > 95 % |
| Tasa de respuesta en 1 h | ¿El paciente reacciona? | > 50 % |
| Tiempo medio de llenado | ¿Se llena a tiempo? | < 4 h |
| Ofertas vencidas | ¿La ventana es adecuada? | < 20 % |
| Dobles reservas | ¿El flujo es seguro? | 0 |

### Importa (negocio)

| Métrica | Qué responde | Objetivo inicial |
|---|---|---|
| Espacios recuperados / semana | ¿Se llenan sillas? | +20 % vs. línea base a 30 días |
| Tasa de recuperación | ¿Se aprovecha el espacio? | ≥ 20 % a 30 días; ≥ 35 % a 90 |
| Ingreso recuperado | ¿Cuánto vale? | citas recuperadas × valor medio de cita del consultorio |
| Inasistencia de citas recuperadas | ¿El paciente llega? | ≤ línea base del consultorio |
| Tiempo manual de la asistente | ¿Se ahorra trabajo? | −50 % en la tarea de llenar espacios |
| Pacientes en lista de espera activa | ¿Hay demanda? | ≥ 10 por consultorio piloto |

> El ingreso recuperado se calcula con el valor medio de cita que aporte el consultorio. **No se inventan precios ni ingresos.**

### Guardrails

- Tasa de baja o queja por ofertas: < 2 %.
- Ofertas por paciente por semana: máximo 3.
- Incidentes de doble reserva: 0.
- Datos clínicos almacenados: 0.
- Ofertas fuera de la ventana 8:00–20:00: 0.

### Cómo se mide

En el MVP demo, la tasa se calcula con las tablas de espacios y ofertas: recuperados / liberados. Para el piloto se instrumentan los eventos espacio_liberado, oferta_enviada, oferta_aceptada, oferta_rechazada, oferta_vencida, espacio_recuperado, espacio_no_recuperado y baja_paciente.

Se reportan semanalmente por consultorio y agregados. La línea base se toma de las 4 semanas previas al piloto.

## 10. Supuestos

- El consultorio tiene pacientes dispuestos a venir antes.
- La asistente puede liberar el espacio en Google Calendar y mover la cita cuando el paciente acepta.
- La duración de la cita está disponible en el evento o se configura un valor por defecto.
- WhatsApp Business y las plantillas están aprobados; los límites y precios se verifican en la documentación oficial.
- El consentimiento se obtiene antes de registrar al paciente en la lista de espera.
- El consultorio puede medir, aunque sea informalmente, cuántos espacios se liberan y cuántos se llenan.

## 11. Riesgos y decisiones

| Riesgo / decisión | Mitigación |
|---|---|
| El espacio se ocupa antes de que el paciente responda | Revalidar contra Calendar antes de ofrecer y antes de confirmar; cancelar oferta |
| Paciente acepta pero no asiste | Medir no-show de recuperadas; no prometer recuperación total |
| Fatiga de ofertas | 2 ofertas por semana por defecto (tope 3); preferencias claras; baja fácil |
| Duración desconocida | Añadir ends_at al evento o configurar duración por defecto |
| Plantilla de WhatsApp no aprobada | Verificar en documentación oficial antes del piloto |
| La asistente no confirma en Calendar | Tarea visible y recordatorio; el espacio no se cierra solo |
| Lista de espera vacía | Mostrar el valor de tener candidatos; onboarding |
| Doble reserva | Una oferta activa por espacio; revalidación y cierre explícito |

**Decisiones tomadas:** duración desde `ends_at` con fallback de 30 min; vencimiento de 30 min (15 min si faltan <2 h); 2 ofertas por semana por defecto y 3 como tope; lista de espera creada solo por la asistente en esta versión. Queda abierto cómo se obtiene el consentimiento en el consultorio.

## 12. Dependencias

- Spec 001: citas, cancelaciones, reprogramaciones, WhatsApp, consentimiento, panel.
- Google Calendar en solo lectura; no se escribe en él.
- WhatsApp Business API y plantilla de «espacio disponible».
- Reloj inyectable para vencimientos y demo.
- Modo demo para probar sin credenciales.

## 13. Criterios de finalización

- CA-1 a CA-8 cumplidos en modo demo.
- Cada RF tiene al menos una prueba automática.
- No hay dobles reservas en las pruebas.
- No se almacenan datos clínicos.
- La línea base y el tablero de métricas están definidos antes del piloto.
- La asistente puede completar el flujo en menos de 2 minutos en una prueba moderada.
