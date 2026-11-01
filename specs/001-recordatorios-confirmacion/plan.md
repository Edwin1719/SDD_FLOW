# Plan técnico — Spec 001

## Estructura de módulos
- app/domain/            → lógica pura, sin E/S: modelos, estados y reglas de envío (RF-4..RF-7, RF-11..RF-15)
- app/services/sync.py     → leer Calendar y reconciliar citas (RF-1..RF-3)
- app/services/dispatch.py → enviar pendientes, reintentos, idempotencia (RF-8, RF-10, RF-16)
- app/services/replies.py  → aplicar respuestas y bajas (RF-9, RF-11..RF-14)
- app/ports/             → interfaces: calendar, messaging, clock
- app/adapters/          → fake_calendar, google_calendar, sim_messaging, whatsapp_cloud, relojes
- app/db/                → esquema y repositorio sobre SQLite
- app/web/               → rutas y plantillas Jinja2 (RF-17)
- app/texts_es.py        → todos los textos en español (mensajes y panel)
- app/config.py, app/main.py → variables de entorno; arranque y selección de adaptadores por modo
- tests/                 → pytest, uno o más tests por RF

## Modelo de datos (SQLite)
Datos mínimos; ningún dato clínico. Fechas en UTC; se convierten a la zona del
consultorio solo para mostrar y para la ventana de envío.

| Tabla | Campos |
|---|---|
| appointments | id, event_id (único), patient_name, phone, starts_at, status, updated_at |
| patients | phone (PK), has_consent, opted_out |
| reminders | id, appointment_id, kind (R1, R2, IMMEDIATE), starts_at_snapshot, scheduled_for, sent_at, state (pending, sent, failed, skipped), attempts, last_error |
| replies | id, appointment_id, action (confirm, reschedule, cancel, optout), received_at, applied |
| sync_state | key, value (guarda el syncToken de Google) |

- `reminders` tiene clave única (appointment_id, kind, starts_at_snapshot) → un recordatorio nunca se duplica (RF-10).
- Versión del esquema en `PRAGMA user_version` (= 1); las tablas se crean al arrancar si no existen.
- El archivo se guarda en `DATABASE_PATH` (por defecto `data/recordatorios.db`); la carpeta `data/` se crea al arrancar si no existe. `.gitignore` excluye `*.db`, así que nunca llega al repositorio.

## Algoritmo de envío (RF-4..RF-7)
Al ingresar o actualizar una cita:
1. R1 = starts_at − 48 h; R2 = starts_at − 24 h.
2. Si la hora cae fuera de 08:00–20:00 (hora del consultorio), pasa al inicio de la siguiente ventana; si ese inicio es posterior a starts_at, se descarta (skipped).
3. Si faltan menos de 48 h se omite R1 y se conserva R2; si faltan menos de 24 h se envía un único IMMEDIATE dentro de la ventana, con la plantilla de R1.
4. Las condiciones de RF-5 (cita no cancelada ni en reprogramación) se evalúan **al momento de enviar**, no al programar.
5. Cita movida en Calendar (RF-3): los pendientes anteriores pasan a skipped, se crean nuevos con la nueva fecha y el estado vuelve a Pendiente.

## Algoritmo de respuestas (RF-9, RF-11..RF-15)
1. La respuesta llega con la cita y la fecha original (identificador del botón). Si llega después de starts_at o la fecha ya cambió → se guarda con applied = false y se ignora.
2. Si no, la última respuesta recibida define el estado (RF-14) y se envía la respuesta automática.
3. Texto «BAJA» (sin distinguir mayúsculas ni espacios) → `opted_out = true`. Desde ese momento no se le envía nada más a ese teléfono: se descartan los pendientes actuales y el envío (`dispatch`) descarta también cualquier recordatorio futuro de un teléfono con `opted_out = true` (por ejemplo, si la cita se mueve y se reprograma).
4. Sin confirmar (RF-15): 3 h después de enviar R2, una cita no Confirmada pasa a Sin confirmar.

## Teléfono (RF-1, RF-2)
Se toma de la línea `Tel:` de la descripción del evento. Tras quitar espacios, guiones y paréntesis debe ser `+` seguido de 8 a 15 dígitos; cualquier otro formato → «Sin teléfono».

## Reglas de no pérdida de datos
- Si la lectura de Google Calendar falla, **no se modifica ni se cancela ninguna cita local**.
- Solo ante un 410 de Google se descarta el syncToken y se repite la sincronización completa, sin borrar el historial de recordatorios ni respuestas.
- Fallo de envío (RF-16): 3 intentos con esperas de 1, 5 y 15 min; agotados, state = failed y la cita pasa a Error de envío. Un reintento nunca crea un segundo envío.

## Decisiones técnicas
- Python 3.12 + FastAPI en vez de Next.js (el planificador en serverless exige un cron externo), Express o Django → un solo proceso y un solo lenguaje (constitución 1).
- HTML en servidor con Jinja2 en vez de una SPA con React → sin cadena de compilación; el panel es una pantalla.
- SQLite (`sqlite3` estándar) en vez de Postgres → sin servicios que administrar. En un host de disco efímero los datos se pierden al reiniciar: en la demo se restauran; para producción real, migrar a un servicio gestionado.
- Planificador en el mismo proceso, revisando cada 60 s con reloj inyectable → permite simular el tiempo en la demo (CA-1).
- Sondeo de Calendar cada 5 min con syncToken en vez de notificaciones push → sin URL pública ni renovación de canales; cumple el «pocos minutos» de RF-3.
- Puertos y adaptadores (constitución 7 y 13). `MODE=demo` (por defecto) usa FakeCalendar, SimulatedMessaging y SimulatedClock; `MODE=real` usa los reales. En demo, `FakeCalendar` también permite **crear, mover y cancelar** citas ficticias (simula editar Google Calendar, RF-3). Los controles `/sim/*` y `/agenda*` no existen en modo real.
- Panel: contraseña única por variable de entorno y cookie de sesión firmada, solo en modo real.
- Seguridad técnica: verificar la firma de cada petición del webhook de WhatsApp; pedir solo el permiso `calendar.events.readonly`; logs con teléfonos enmascarados (`+57******1234`) y sin nombres; secretos solo en variables de entorno (`.env.example` sin valores).
- Valores iniciales configurables, a validar con la doctora: ventana de envío, 3 h para Sin confirmar, reintentos.
- Dependencias de ejecución: fastapi, uvicorn, jinja2, python-multipart, httpx. Solo modo real: google-api-python-client, google-auth-oauthlib. Desarrollo: pytest y ruff (linter + formatter, `line-length = 88`, estilo uniforme sin el límite arbitrario de 79 de pycodestyle). Cualquier otra se justifica aquí; fijar versiones al instalar.
- Identidad visual y tipografía: la skill `brand-design` define la paleta (blanco + azul corporativo), el logo de diente y la composición del panel. La fuente Atkinson Hyperlegible se carga vía Google Fonts con `font-display: swap` y respaldo `system-ui`; no es una dependencia de Python.
- Variables: MODE, DATABASE_PATH, CLINIC_TIMEZONE, SEND_WINDOW_START/END, SYNC_INTERVAL_MINUTES, MAX_SEND_ATTEMPTS, UNCONFIRMED_AFTER_HOURS, PANEL_PASSWORD, SESSION_SECRET, GOOGLE_*, WHATSAPP_*.

## Rutas web
| Ruta | Modo | Función |
|---|---|---|
| GET / | ambos | Panel: «Requieren atención» y «Agenda» (RF-17) |
| GET /health | ambos | Comprobación de estado |
| GET, POST /webhooks/whatsapp | real | Verificación inicial de Meta y recepción de respuestas |
| GET /sim | demo | Conversaciones simuladas y botones «responder como paciente» |
| POST /sim/reply, /sim/clock/advance, /sim/fail-next-send, /sim/reset | demo | Responder, adelantar la hora, forzar un fallo (CA-5), restaurar datos |
| GET /agenda | demo | Agenda simulada (Google Calendar ficticio): vista por día y controles crear/mover/cancelar (CA-7) |
| POST /agenda/create, /agenda/move, /agenda/cancel | demo | Crear, mover y cancelar citas ficticias; disparan sincronización (RF-3) |

Cada botón de WhatsApp lleva un identificador con la cita, la fecha original y la acción (por ejemplo `appt:<id>:<fecha>:confirm`). Las plantillas `reminder_48h` y `reminder_24h` usan los textos de la spec 4.3 con tres botones de respuesta rápida y deben ser aprobadas por Meta.

## Estrategia de pruebas
- Dominio con reloj inyectado: cálculo de envíos (48 h, 24 h, menos de 48 h, menos de 24 h, ventana horaria, cambio de horario) y transiciones, incluido confirmar y luego cancelar.
- Servicios con adaptadores simulados: sincronización (cita nueva, movida, cancelada, error de lectura sin pérdida de datos), envío con reintentos sin duplicados, baja y consentimiento.
- Web: panel con cada estado en ancho de celular; rutas `/sim` ausentes en modo real.
- Aceptación: un test por criterio CA-1 a CA-5 en modo demo.
- Ninguna prueba llama a WhatsApp ni a Google (constitución 8).

## Fuentes verificadas (consultadas el 29 de octubre de 2026)
| Dato | Fuente | Fiabilidad |
|---|---|---|
| Sincronización incremental con syncToken; 410 obliga a repetir la sincronización completa; los resultados incluyen entradas eliminadas | developers.google.com/calendar/api/guides/sync | Oficial |
| Alta de la Cloud API (cuenta de desarrollador, app de Meta, portafolio de negocio, webhook); fuera de la ventana de 24 h solo plantillas | developers.facebook.com/documentation/business-messaging/whatsapp/get-started | Oficial |
| Leer eventos con `calendar.events.readonly` es un permiso sensible que exige verificación OAuth en producción | developer.nylas.com/docs/cookbook/calendar/google-calendar-oauth/ | Tercero: confirmar en la documentación oficial de Google |
| Webhooks: verificación con hub.verify_token / hub.challenge y firma X-Hub-Signature-256 | SDKs de terceros (chat-sdk.dev, pkg.go.dev) | Tercero: confirmar en la documentación oficial de Meta |
| Botones de respuesta: máximo 3, título de hasta 20 caracteres; las plantillas admiten botones de respuesta rápida | SDKs de terceros (chat-sdk.dev, packagist.org) | Tercero: confirmar en la documentación oficial |

**Pendiente de verificar (sin cifras hasta confirmarlas):** precio por mensaje y categorías de plantilla, límites de envío, criterios y plazos de aprobación de plantillas, coexistencia por país, tamaño máximo del identificador de botón, y la aprobación de la app de Google para producción. Consultar la página oficial de precios y la documentación de plantillas de Meta, y la página oficial de scopes de Google.
