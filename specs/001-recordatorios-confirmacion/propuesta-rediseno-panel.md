# Propuesta — Rediseño del Panel y la Agenda

**Estado:** ejecutada el 2026-11-01. Se ajustaron T10–T21 sin crear tareas nuevas.
**Fecha:** 2026-11-01
**Alcance:** navegación, Panel, Agenda, edición de teléfono y correcciones críticas asociadas.

## 1. Qué se propone

Reemplazar la agenda semanal en cuadrícula del Panel por una **agenda de día en filas anchas**, con **«Requieren atención» arriba y accionable**, una **barra superior en escritorio** y la **barra inferior actual en celular**. Añadir la **edición de nombre y teléfono** de una cita, tanto en la agenda simulada como desde la lista de atención.

El objetivo no es solo que se vea mejor: que la asistente pueda resolver en la misma pantalla lo que el Panel le está señalando.

## 2. Diagnóstico

1. **La grilla no funciona como agenda.** A 360 px son 7 columnas × 13 filas = 91 celdas para 4 citas; las tarjetas quedan de 53 px, los nombres se parten («Pére / z») y los estados largos se salen y quedan tapados por la columna vecina.
2. **Las citas fuera de 8:00–20:00 se fuerzan a la fila de 8:00.** Los datos sembrados a las 02:05/04:05 se amontonan en la primera fila y el resto de la grilla queda vacío. La posición no representa la hora.
3. **«Sin teléfono» es una vía muerta.** No hay forma de editar el teléfono; la fila de atención no tiene acción; y aunque se corrija en Google Calendar, la sincronización no actualiza el teléfono porque solo reacciona a cambios de fecha/hora.
4. **La barra lateral de escritorio es demasiado pesada.** 232 px de azul a toda altura + panel de 640 px dejan media pantalla vacía. En celular no existe sidebar (hay barra inferior), pero en escritorio el conjunto no se siente como una herramienta clínica.
5. **La spec y la skill de marca se contradicen.** La spec 4.4 pide grilla semanal; la skill dice que cada cita sea una fila de lista, no una tarjeta.

## 3. Decisiones propuestas

| # | Decisión | Recomendación |
|---|---|---|
| D1 | El Panel deja de mostrar la semana completa | Mostrar «Requieren atención» + «Agenda de hoy» |
| D2 | La Agenda pasa a vista de día, con filas | Día en celular y escritorio; sin grilla 7×13 |
| D3 | Navegación | Barra superior en escritorio; barra inferior en celular |
| D4 | Teléfono | Editable en demo; en real, enlace a Google Calendar + sync |
| D5 | Datos de la demo | Sembrar en hora de Bogotá y en horario del consultorio |

## 4. Navegación

### Escritorio (≥ 1024 px)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [logo] Consultorio de la Dra. Laura     Panel   Agenda   Simulador  [Demo] │
├─────────────────────────────────────────────────────────────────────────┤
│  contenido a ancho completo, máximo ~1200 px                            │
└─────────────────────────────────────────────────────────────────────────┘
```

- Barra blanca de 64 px, borde inferior.
- Logo y nombre a la izquierda.
- Tres pestañas horizontales; la activa en azul con subrayado de 2 px.
- Badge «Demo · datos ficticios» a la derecha.
- Se elimina la barra lateral azul.

### Celular (< 768 px)

- Cabecera compacta de 56 px: logo + nombre corto + badge.
- Barra inferior fija con **Panel / Agenda / Simulador** (se conserva la actual).
- Sin menú hamburguesa: para tres destinos, la barra inferior está al alcance del pulgar y muestra siempre dónde está la usuaria.

## 5. Panel

### Orden

1. **Título** «Panel» (h1) y fecha de hoy.
2. **Resumen**: Citas hoy · Requieren atención · Confirmadas hoy.
3. **Requieren atención** inmediatamente debajo, con acción por fila.
4. **Agenda de hoy**: filas anchas con navegación de día.
5. **Así funciona**, al final y más compacto.

### Escritorio

```
Citas hoy 3        Requieren atención 2        Confirmadas 1

Requieren atención
09:00  Luis Pérez     Sin teléfono        [Agregar teléfono]
11:30  Ana Gómez      Reprogramación      [Abrir en agenda]

Agenda de hoy   [‹]  Lunes 2 de noviembre  [›]   [Ver semana]
08:00  —
09:00  Luis Pérez     Pendiente   +57...   [Editar] [Mover]
11:30  Ana Gómez      Confirmada  +57...   [Editar] [Mover]
```

### Celular

```
Citas hoy 3 | Atención 2 | Confirmadas 1

Requieren atención
09:00  Luis Pérez
       Sin teléfono        [Agregar teléfono]

Hoy · lunes 2 de noviembre
08:00  —
09:00  Luis Pérez
       Pendiente · +57...
       [Editar]  [Mover]
11:30  Ana Gómez
       Confirmada · +57...
       [Editar]  [Mover]
```

### Reglas

- Cada cita es una **fila**, no una tarjeta. Sin anchos de 53 px.
- La fila muestra hora, nombre, estado, teléfono y acciones.
- Si no hay citas: «Hoy no hay citas.» con un enlace a la Agenda.
- Si no hay atención: «Nada pendiente. Todo al día.»
- La barra «Responder como paciente» **se retira del Panel**; queda solo en el Simulador. El Panel es de la asistente.
- En demo, cada fila de atención tiene una acción concreta: **Agregar teléfono**, **Ver en agenda** o **Abrir en Google Calendar** (real).

## 6. Agenda

- **Vista de día** por defecto, con franja de 7 días para cambiar de fecha.
- Línea de tiempo de 8:00 a 20:00, pero las citas se muestran como filas anchas, no como tarjetas dentro de celdas.
- En escritorio, dos columnas: agenda del día a la izquierda y resumen/atención a la derecha.
- En celular, una columna; la franja de días se desliza horizontalmente.
- Cabecera del día: «Lunes 2 de noviembre», con «Hoy» y flechas.
- Acciones por cita: **Editar** (nombre y teléfono), **Mover** (fecha/hora) y **Cancelar**.
- Citas fuera de 8:00–20:00: se muestran en una sección **«Fuera de horario»** al final, nunca encima de otra cita.
- «Nueva cita» se mantiene; en celular se puede plegar para no ocupar la primera pantalla.
- La vista **Semana** queda fuera de esta iteración. Si más adelante se necesita, se añade como pestaña secundaria en escritorio.

## 7. Edición de teléfono

### Modo demo

- Botón **Editar** en cada fila de la agenda y en la fila de atención.
- Formulario con nombre y teléfono; valida con `extract_phone`.
- Al guardar un teléfono válido:
  - la cita deja de estar «Sin teléfono» y pasa a «Pendiente»;
  - se programan sus recordatorios;
  - desaparece de «Requieren atención»;
  - el Panel y la Agenda se actualizan.
- Si el teléfono es inválido, se muestra un error en español y no se guarda.

### Modo real

- La app no escribe en Google Calendar: es la fuente de verdad y el permiso es de solo lectura.
- La fila de atención muestra **«Corregir en Google Calendar»** con una instrucción breve: añadir la línea `Tel: +57...` en la descripción del evento.
- La sincronización debe actualizar **nombre y teléfono**, no solo la fecha/hora. Si aparece un teléfono válido, la cita vuelve a «Pendiente» y se programan recordatorios.
- Si se quita el teléfono, pasa a «Sin teléfono» y se descartan los pendientes.

## 8. Datos y zona horaria

- Configurar `CLINIC_TIMEZONE=America/Bogota` en el entorno de la demo y documentarlo.
- Añadir `tzdata` a `requirements.txt` para que funcione en Windows.
- Sembrar las citas en hora local del consultorio y en horario real: por ejemplo, mañana 09:00, 10:30 y 15:00; no a las 02:05.
- El reloj simulado y el Panel deben mostrar la hora del consultorio, no UTC.
- Si una cita cae fuera de 8:00–20:00, se muestra en «Fuera de horario», no se recoloca.

## 9. Correcciones críticas que conviene incluir

Estas no son de diseño, pero sin ellas el rediseño se vería mejor y seguiría fallando en lo importante:

1. **Consentimiento y baja.** No enviar respuesta automática si el paciente no tiene consentimiento o pidió la baja. Añadir tests para «BAJA y luego Confirmo» y «sin consentimiento y luego Confirmo».
2. **Textos de los recordatorios.** Usar los textos de la spec 4.3 en lugar de «Recordatorio R2»; centralizarlos en `texts_es.py` y comprobar el cuerpo en un test.
3. **Recordatorios obsoletos.** No enviar un recordatorio si la cita ya empezó; al adelantar el reloj, descartar los que llegaron tarde.

Recomiendo hacerlas en el mismo lote: son cambios pequeños y afectan la credibilidad de la demo.

## 10. Cambios en la spec

| Documento | Cambio |
|---|---|
| `spec.md` 4.4 | Sustituir la grilla semanal del Panel por «atención + agenda de hoy»; navegación superior en escritorio; filas, no tarjetas; edición de teléfono |
| `spec.md` RF-2 | Añadir la corrección del teléfono en demo y el reflejo del cambio en real |
| `spec.md` RF-3 | Incluir cambios de nombre y teléfono, no solo fecha/hora |
| `spec.md` nuevo RF-18 | «El sistema permitirá corregir nombre y teléfono en la agenda simulada y reflejará los cambios hechos en Google Calendar» |
| `spec.md` nuevo CA-8 | Panel y Agenda a 360 px sin grilla 7×13, sin cortes de texto, atención visible antes de la agenda |
| `spec.md` nuevo CA-9 | Agregar un teléfono válido a una cita «Sin teléfono» la devuelve a «Pendiente», la saca de atención y programa recordatorios |
| `plan.md` | Rutas `/agenda/edit`, campos actualizables, `FakeCalendar.update_event`, día como vista principal |
| `SKILL.md` | Barra superior en escritorio; composición del Panel; filas en vez de tarjetas; contraste del badge; h1 |

## 11. Cambios técnicos

- `app/db/repository.py`: `update_appointment` acepta `patient_name` y `phone`.
- `app/adapters/fake_calendar.py`: `update_event(event_id, patient_name, phone)`.
- `app/services/sync.py`: comparar todos los campos; al cambiar el teléfono, reprogramar recordatorios y ajustar el estado.
- `app/web/agenda_routes.py`: nueva ruta POST `/agenda/edit`.
- `app/web/routes.py`: nuevo modelo de la vista de Panel (atención + día).
- Plantillas: `panel.html`, `agenda.html`, `_navegacion.html`.
- `styles.css`: barra superior, filas, franja de días, formulario de edición.
- Tests: repositorio, sincronización, edición, Panel, Agenda, aceptación.

## 12. Tareas existentes que se ajustan (no se crean tareas nuevas)

| Tarea existente | Ajuste | Hecho cuando |
|---|---|---|
| T10 | Actualizar la skill de marca: barra superior, filas en vez de tarjetas, contraste del badge, h1 | La skill describe el nuevo panel y la nueva navegación |
| T11 | Panel: «Requieren atención» arriba y accionable, próximas citas en filas, sin grilla, h1 | Tests de estados y revisión a 360/1440 |
| T12 | Simulador: responder solo si hay teléfono y consentimiento; aviso de fallo armado; nombres en los mensajes | Cada control sigue funcionando y los casos imposibles no se ofrecen |
| T13 | Aceptación: CA-1 a CA-9, incluidos panel sin grilla y edición de teléfono | Cada criterio tiene su test y `pytest -q` pasa completo |
| T17 | README: nueva navegación, panel de día y edición de teléfono | Una persona ajena sigue el README sin ayuda |
| T19 | Rediseño visual: barra superior, agenda de día, filas, sin barra lateral azul | Revisión a 360 y 1440 sin desbordamiento |
| T20 | Agenda simulada: vista de día, editar nombre/teléfono, crear/mover/cancelar | «Sin teléfono» → «Pendiente» y recordatorios programados |
| T21 | Navegación: barra superior en escritorio, barra inferior en celular | 360 px y 1440 px sin solapamientos; ítem activo visible |

Las tareas T1–T9, T14–T16 y T18 no cambian. No se añaden T22 ni siguientes.

## 13. Criterios de aceptación

- A 360 px no hay grilla de 7 columnas; cada cita es una fila a ancho completo.
- Ningún nombre se parte por letras y ningún estado se corta.
- «Requieren atención» se ve antes que la agenda, o en la primera pantalla.
- En escritorio no hay barra lateral azul; el contenido usa el ancho disponible.
- «Sin teléfono» ofrece **Agregar teléfono**; al guardar un número válido y confirmar el consentimiento, la cita sale de atención y se programan recordatorios. Si no hay consentimiento, queda «Sin consentimiento».
- Corregir nombre/teléfono en el calendario simulado se refleja en el Panel.
- `pytest -q` pasa completo, incluyendo CA-1 a CA-9.
- No se modifica Google Calendar en modo real.

## 14. Fuera de alcance

- Cablear el modo real (Google/WhatsApp).
- Autenticación y despliegue.
- Vista «Semana» (se evalúa después).
- Facturación, expediente, etc.

## 15. Decisiones que se aplican salvo que digas lo contrario

1. Panel «atención + próximas citas» y Agenda de día.
2. Barra superior en escritorio + barra inferior en celular.
3. Se incluyen las correcciones críticas del punto 9.
4. La vista «Semana» queda fuera por ahora.

## 16. Al ejecutar

Ajusto `spec.md`, `plan.md`, `SKILL.md` y `tasks.md` reutilizando T10–T21. Después implemento y ejecuto `pytest -q`. Al final te muestro el resultado y marco las tareas existentes, sin agregar tareas nuevas.
