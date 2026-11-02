# Tareas — Spec 001

Una tarea a la vez, en orden. Cada una termina con sus tests en verde (constitución 4).

- [x] T1. Esqueleto del proyecto: paquete `app/` con sus subcarpetas, `tests/`,
      `requirements.txt`, `.env.example` sin valores reales. (RF: —)
      Hecho cuando: `pytest -q` corre (0 tests) sin errores y `uvicorn app.main:app`
      arranca mostrando `/health`.
- [x] T2. Configuración, puertos y relojes: `config.py` (variables del plan),
      interfaces `CalendarPort`, `MessagingPort`, `ClockPort`, `SystemClock` y
      `SimulatedClock`. (RF-7)
      Hecho cuando: tests de carga de configuración (modo demo por defecto) y de
      avance del reloj simulado en verde.
- [x] T3. Base de datos: esquema SQLite, versión del esquema y repositorio.
      (RF-10)
      Hecho cuando: tests de creación al arrancar (incluida la carpeta `data/`), reapertura sin perder datos y
      rechazo de un recordatorio duplicado (misma cita, tipo y fecha) en verde.
- [x] T4. Dominio — estados y respuestas: transiciones de la cita, última respuesta
      manda, Sin confirmar, Confirmada se mantiene. (RF-11, RF-12, RF-13, RF-14, RF-15)
      Hecho cuando: tests de confirmar, reprogramar, cancelar, confirmar y luego
      cancelar, y sin confirmar en verde.
- [x] T5. Dominio — cálculo de envíos: R1, R2, inmediato, ventana de 8:00 a 20:00 y
      cambio de horario. (RF-4, RF-5, RF-6, RF-7)
      Hecho cuando: tests de 48 h, 24 h, menos de 48 h, menos de 24 h, hora fuera de
      ventana y cambio de horario en verde.
- [x] T6. Sincronización con calendario simulado: `FakeCalendar` con pacientes
      ficticios, lectura del teléfono (`+` y 8 a 15 dígitos) y reconciliación de
      citas nuevas, movidas y canceladas. (RF-1, RF-2, RF-3)
      Hecho cuando: tests de cita nueva, movida, cancelada, sin teléfono, teléfono mal
      escrito y fallo de lectura sin perder datos locales en verde.
- [x] T7. Envío de recordatorios: `SimulatedMessaging`, consentimiento, reintentos
      y estado Error de envío. (RF-4, RF-5, RF-8, RF-10, RF-16)
      Hecho cuando: tests de envío con consentimiento, sin consentimiento, reintento
      sin duplicado y fallo tras agotar reintentos en verde.
- [x] T8. Respuestas del paciente: aplicar respuestas, baja y respuestas tardías.
      (RF-9, RF-11, RF-12, RF-13, RF-14)
      Hecho cuando: tests de cada botón, baja con «BAJA», respuesta posterior a la
      cita y respuesta a una fecha ya cambiada en verde.
- [x] T9. Planificador y arranque en modo demo: tarea de fondo que sincroniza y envía
      cada minuto, y marca Sin confirmar. (RF-4, RF-5, RF-15)
      Hecho cuando: test que adelanta el reloj simulado y comprueba R1, R2 y Sin
      confirmar sin esperar, en verde.
- [x] T10. Skill `brand-design`: identidad visual y navegación del panel
      (barra superior, filas en vez de tarjetas, badge con contraste y checklist).
      (RF: —)
      Hecho cuando: la skill describe la nueva navegación y composición y el
      usuario la aprueba.
- [x] T11. Panel de la asistente: «Requieren atención» accionable y próximas
      citas en filas, sin grilla semanal, con `h1` y edición de teléfono desde la
      atención. (RF-2, RF-8, RF-17, RF-18)
      Hecho cuando: cada estado se ve con texto, símbolo y color; no hay cortes ni
      palabras partidas a 360 px; la atención aparece antes que la agenda.
- [x] T12. Simulador del modo demo: conversaciones con nombre del paciente,
      «responder como paciente» solo si hay teléfono y consentimiento, adelantar
      la hora, aviso de fallo armado, restaurar datos y badge DEMO. (RF-4, RF-9,
      RF-12, RF-13, RF-16)
      Hecho cuando: los controles funcionan, los casos imposibles no ofrecen
      botones y las rutas `/sim` no existen en modo real.
- [x] T13. Pruebas de aceptación CA-1 a CA-9 recorriendo el flujo completo en
      modo demo, incluidos panel sin grilla y corrección de teléfono. (Todos)
      Hecho cuando: cada criterio tiene su test y `pytest -q` pasa completo.
- [x] T14. Adaptador real de Google Calendar: lectura con permiso de solo lectura,
      `syncToken` y manejo del 410. (RF-1, RF-3)
      Hecho cuando: tests con respuestas simuladas en verde; ninguna llamada real.
- [x] T15. Adaptador real de WhatsApp y webhook: envío de plantillas, verificación
      inicial y comprobación de firma. (RF-4, RF-11, RF-12, RF-13)
      Hecho cuando: tests con respuestas simuladas, incluida firma inválida
      rechazada, en verde; ninguna llamada real.
- [x] T16. Contraseña del panel en modo real. (RF-17)
      Hecho cuando: tests de acceso sin sesión, con contraseña correcta e incorrecta
      en verde.
- [x] T17. README y repositorio: nueva navegación, panel de atención, agenda de
      día y edición de teléfono; cómo ejecutar la demo y activar los servicios
      reales. (Todos)
      Hecho cuando: una persona ajena sigue el README, ejecuta la demo y completa
      el flujo agendar → recordatorio → responder → corregir teléfono sin ayuda.
- [ ] T18. (Opcional) Demo desplegada en Render + pruebas en tiempo real.
      Despliegue: GitHub → Render > New > Web Service → Build `pip install -r requirements.txt` → Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; `MODE=demo` (sin credenciales).
      Pruebas reales (`MODE=real`): requiere Google (`calendar.events.readonly`, quizá verificación OAuth) + Meta (WhatsApp Business y plantillas `reminder_48h`/`reminder_24h` aprobadas con 3 botones); credenciales GOOGLE_*/WHATSAPP_* en variables de entorno.
      Verificar contra el problema del cliente: (1) recordatorios salen a 48 h y 24 h; (2) confirmar/cancelar/reprogramar con un toque; (3) la asistente ve cancelaciones, reprogramaciones y fallos en «Requieren atención»; (4) inasistencia de ~30 % a <10 % (métrica posterior con la doctora).
      Hecho cuando: la URL abre el panel con el banner DEMO y el flujo funciona, y en `MODE=real` se comprueba en tiempo real que resuelve los problemas del cliente.
- [x] T19. Rediseño visual: barra superior blanca con logo y navegación; Panel
      con atención primero y próximas citas en filas; Agenda de día; sin barra
      lateral azul ni grilla 7×13; badge con contraste. (RF-17, CA-6, CA-8)
      Hecho cuando: tests del panel y del simulador en verde y revisión visual a
      360 y 1440 px sin desbordamiento ni texto cortado.
- [x] T20. Agenda simulada interactiva: `FakeCalendar` con crear/mover/editar/
      cancelar, vista de día en rutas demo `/agenda`, edición de nombre y
      teléfono y sincronización al guardar. (RF-2, RF-3, RF-4, RF-6, RF-18,
      CA-7, CA-9)
      Hecho cuando: tests de crear, mover, editar y cancelar una cita ficticia y
      su efecto en el panel y los recordatorios en verde; rutas `/agenda*`
      ausentes en modo real.
- [x] T21. Navegación y flujo guiado del demo: barra superior (escritorio) y
      barra inferior (celular) con Panel/Agenda/Simulador, barra blanca, y
      recorrido guiado «Así funciona» en el panel con enlaces a cada vista.
      (CA-6, CA-8)
      Hecho cuando: navegación visible en las tres vistas a 360 px y en
      escritorio con el ítem activo en azul, flujo guiado enlazando a Agenda y
      Simulador, y tests en verde.
