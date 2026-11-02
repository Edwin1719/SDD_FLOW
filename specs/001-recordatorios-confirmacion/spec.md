# Spec 001 — Recordatorios escalonados con confirmación de un toque

## 1. Contexto y problema

La Dra. Laura tiene un consultorio dental pequeño con una asistente. Agenda las
citas en Google Calendar y ese flujo funciona bien.

- Cerca del **30 % de los pacientes no llegan** y esos espacios se pierden.
- La asistente dedica buena parte de la mañana a enviar **recordatorios por
  WhatsApp uno por uno**.
- Cuando un paciente no va a asistir, el consultorio suele enterarse tarde o
  nunca, y no alcanza a recuperar el espacio.

**Objetivo de esta spec:** que cada paciente reciba recordatorios automáticos,
pueda confirmar, reprogramar o cancelar con un toque, y que la asistente vea en
un solo lugar el estado de cada cita y qué necesita su atención.

Un solo feature por spec. El seguimiento de tratamientos de varias sesiones, la
lista de espera y las métricas quedan para specs posteriores.

## 2. Usuarios

- **Asistente (usuaria principal):** no es técnica; usa el panel desde el
  celular. Debe saber qué citas están confirmadas y cuáles requieren acción.
- **Paciente:** solo interactúa por WhatsApp; nunca inicia sesión en nada.
- **Dra. Laura:** consulta el estado de su agenda.

## 3. Historias de usuario

- **H1:** Como paciente quiero recibir un recordatorio de mi cita y responder
  con un toque, para no olvidarla o avisar si no podré ir.
- **H2:** Como asistente quiero ver el estado de confirmación de cada cita, para
  saber a quién llamar y dejar de enviar recordatorios a mano.
- **H3:** Como asistente quiero enterarme cuando un paciente cancela o pide
  reprogramar, para liberar el espacio en el calendario y poder aprovecharlo.

## 4. Diseño de la solución (funcional)

### 4.1 Flujo de una cita

```
Cita en Google Calendar
   └─► 48 h antes: recordatorio 1 ──► Confirmo ──────► Confirmada
                                  ├─► Reprogramar ───► Reprogramación solicitada (fin de recordatorios)
                                  ├─► Cancelar ──────► Cancelada por paciente (fin de recordatorios)
                                  └─► sin respuesta ─► sigue en espera
   └─► 24 h antes: recordatorio 2 (también si ya confirmó; no si reprogramó o canceló)
                                  ├─► Confirmo / Reprogramar / Cancelar → igual que arriba
                                  └─► sin respuesta:
                                        · si ya estaba Confirmada → sigue Confirmada
                                        · si no → Sin confirmar (alerta a la asistente)
```

### 4.2 Estados de una cita

| Estado | Significado |
|---|---|
| Pendiente | Cita futura sin ningún recordatorio enviado |
| Recordatorio enviado | Se envió el aviso de 48 h o de 24 h y se espera respuesta |
| Confirmada | El paciente pulsó «Confirmo» (puede cambiar su respuesta hasta la hora de la cita) |
| Reprogramación solicitada | El paciente pulsó «Reprogramar» |
| Cancelada por paciente | El paciente pulsó «Cancelar» |
| Sin confirmar | Pasó el recordatorio de 24 h y la cita no fue confirmada |
| Error de envío | No se pudo entregar un recordatorio |
| Sin consentimiento | El paciente no tiene consentimiento registrado; no se le envía nada |
| Sin teléfono | El evento no tiene un teléfono válido; no se le envía nada |

### 4.3 Mensajes al paciente

Neutros, sin detalles clínicos. Los textos exactos son:

**Recordatorio 1 (48 h antes)**
> Hola {nombre}, te recordamos tu cita en el consultorio de la Dra. Laura el
> {día} {fecha} a las {hora}. ¿Nos confirmas?
> Botones: **Confirmo** · **Reprogramar** · **Cancelar**

**Recordatorio 2 (24 h antes)**
> Hola {nombre}, tu cita en el consultorio de la Dra. Laura es mañana,
> {día} {fecha} a las {hora}. ¿Sigues pudiendo asistir?
> Botones: **Confirmo** · **Reprogramar** · **Cancelar**

**Recordatorio inmediato** (cita agendada con menos de 24 h de anticipación, RF-6)
> Usa el mismo texto y los mismos botones del Recordatorio 1.

**Respuestas automáticas**
- Confirmo: «¡Gracias! Te esperamos.»
- Reprogramar: «Entendido. La asistente te contactará para elegir una nueva fecha.»
- Cancelar: «Listo, cancelamos tu cita. Si quieres agendar otra, escríbenos.»

### 4.4 Panel de la asistente (una pantalla, pensada para celular)

1. **Resumen** (arriba): tres cifras de un vistazo — citas de hoy, citas que
   requieren atención y citas confirmadas hoy.
2. **Requieren atención** (inmediatamente debajo del resumen): citas en estado
   Reprogramación solicitada, Cancelada por paciente (espacio liberado), Sin
   confirmar, Error de envío, Sin teléfono y Sin consentimiento. Cada fila
   muestra hora, nombre, estado y una acción: **Agregar teléfono** (sin
   teléfono, en demo), **Ver en agenda** o **Corregir en Google Calendar**
   (modo real). No es una lista pasiva.
3. **Agenda de hoy** (debajo): si hoy hay citas, una lista de filas con hora,
   nombre, estado y teléfono; si no hay citas hoy, muestra las **próximas
   citas** con su fecha. No hay grilla semanal en el Panel.

Cada cita es una **fila de lista**, no una tarjeta: hora, nombre, estado y
teléfono en una línea legible. En modo demo la fila permite **Editar** nombre y
teléfono y **Mover** a otra fecha/hora; en modo real la edición se hace en
Google Calendar.

Navegación: **barra superior** con logo, Panel, Agenda y Simulador en
escritorio; **barra inferior** con los mismos tres destinos en celular. El
Panel tiene un `h1` («Panel») y la fecha del día.

El panel aplica de forma completa la identidad visual de la skill
`brand-design`: tipografía cargada, superficies y filas con la jerarquía
definida, controles estilizados, foco visible y objetivos táctiles de 44 px.

La app **no modifica Google Calendar**: la asistente reprograma, edita o elimina
las citas allí, como hoy, y el sistema refleja el cambio. En modo demo, la
agenda simulada sí permite editar porque representa el calendario.

### 4.5 Modo demo

El proyecto debe poder ejecutarse sin credenciales (ver constitución, principio
13). En modo demo:
- Las citas provienen de un calendario de ejemplo con pacientes ficticios.
- Los mensajes no salen a WhatsApp: se muestran en el simulador como una
  conversación simulada, y desde allí se puede **responder como el paciente**
  pulsando los botones.
- Se puede **avanzar la fecha y hora simuladas** para ver los recordatorios
  de 48 h y 24 h sin esperar.
- Se muestra una **agenda simulada** que representa Google Calendar: una vista
  por día de las citas ficticias con controles para **crear, mover, editar y
  cancelar** citas ficticias. Al crearlas aparecen en el panel y programan sus
  recordatorios; al moverlas se descartan los pendientes y el ciclo se
  reinicia; al cancelarlas no se envían más recordatorios (RF-3). En modo demo
  la edición permite corregir el nombre y el teléfono.
- Las tres vistas del modo demo (panel, agenda simulada y simulador) se enlazan
  con una **navegación fija**: barra superior en escritorio y barra inferior en
  celular.
- El panel muestra un recorrido guiado **«Así funciona»** con los pasos del
  ciclo (agendar → recordatorio → respuesta → estado) y enlaces a cada vista,
  para que la demo demuestre el valor de un vistazo.

## 5. Requisitos funcionales (EARS)

### Lectura de la agenda
- **RF-1:** EL SISTEMA leerá las citas futuras desde Google Calendar y tomará
  de cada una el nombre del paciente, la fecha y hora, y el teléfono, que
  estará en la descripción del evento en una línea con el formato
  `Tel: +<código de país><número>`.
- **RF-2:** SI una cita no tiene teléfono con ese formato, ENTONCES EL SISTEMA
  la mostrará en «Requieren atención» como «Sin teléfono» y no enviará
  recordatorios. En modo demo la asistente podrá corregir el teléfono desde la
  agenda; en modo real lo corregirá en Google Calendar y el sistema reflejará
  el cambio.
- **RF-3:** CUANDO una cita se cancele o cambie de fecha, hora, nombre o
  teléfono en Google Calendar, EL SISTEMA descartará los recordatorios
  pendientes de la fecha anterior, y si fue movida reiniciará el ciclo con la
  nueva fecha en estado Pendiente. Si aparece un teléfono válido y el paciente
  tiene consentimiento registrado, la cita volverá a Pendiente y se programarán
  sus recordatorios; si no, quedará Sin consentimiento. El cambio se reflejará
  en pocos minutos (el plazo exacto se fija en el plan).

### Envío de recordatorios
- **RF-4:** CUANDO falten 48 h para una cita en estado Pendiente y con
  consentimiento, EL SISTEMA enviará el recordatorio 1.
- **RF-5:** CUANDO falten 24 h para una cita que no esté Cancelada por
  paciente ni en Reprogramación solicitada, EL SISTEMA enviará el
  recordatorio 2, incluso si la cita ya está Confirmada.
- **RF-6:** SI la cita se agenda con menos de 48 h de anticipación, ENTONCES
  EL SISTEMA enviará solo los recordatorios que aún estén a tiempo; si faltan
  menos de 24 h, enviará un único recordatorio inmediato.
- **RF-7:** EL SISTEMA enviará los mensajes solo dentro de la ventana de envío
  definida en el supuesto S1; los que correspondan fuera de ella se enviarán al
  inicio de la siguiente ventana.
- **RF-8:** EL SISTEMA no enviará mensajes a pacientes sin consentimiento
  registrado, y los mostrará como «Sin consentimiento».
- **RF-9:** SI el paciente responde con una solicitud de baja (por ejemplo
  «BAJA»), ENTONCES EL SISTEMA no le enviará más mensajes.
- **RF-10:** EL SISTEMA no enviará el mismo recordatorio dos veces para la misma
  cita, aunque reintente un envío o se reinicie.

### Respuestas del paciente
- **RF-11:** CUANDO el paciente pulse «Confirmo», EL SISTEMA marcará la cita
  como Confirmada y responderá con el mensaje correspondiente. La confirmación
  no cancela el recordatorio de 24 h.
- **RF-12:** CUANDO el paciente pulse «Reprogramar», EL SISTEMA marcará la cita
  como Reprogramación solicitada, responderá y la mostrará en «Requieren
  atención».
- **RF-13:** CUANDO el paciente pulse «Cancelar», EL SISTEMA marcará la cita
  como Cancelada por paciente, responderá y la mostrará en «Requieren
  atención» como espacio liberado.
- **RF-14:** SI el paciente pulsa más de un botón para la misma cita (por
  ejemplo, confirma y después cancela), ENTONCES EL SISTEMA aplicará la última
  respuesta recibida antes de la hora de la cita.

### Seguimiento y errores
- **RF-15:** CUANDO pase el recordatorio 2 sin respuesta y la cita no esté
  Confirmada, EL SISTEMA la marcará como Sin confirmar y la mostrará en
  «Requieren atención» (el plazo de espera se fija en el plan).
- **RF-16:** SI un envío falla, ENTONCES EL SISTEMA lo reintentará un número
  limitado de veces y, si sigue fallando, marcará la cita como Error de envío y
  la mostrará en «Requieren atención». Ningún fallo debe pasar inadvertido.

### Panel
- **RF-17:** EL SISTEMA mostrará a la asistente el panel descrito en 4.4,
  utilizable desde un celular, con el estado de cada cita legible por texto
  además de por color.
- **RF-18:** EL SISTEMA permitirá corregir nombre y teléfono de una cita en la
  agenda simulada (modo demo) y reflejará los cambios de nombre o teléfono
  hechos en Google Calendar (modo real), sin modificar el calendario.

## 6. Criterios de aceptación (verificables en modo demo)

Nueve criterios, todos comprobables en modo demo (sección 4.5).

**CA-1 — Recordatorios escalonados** (RF-4, RF-5, RF-10)
- Dado una cita futura con teléfono y consentimiento, cuando la fecha simulada
  llega a 48 h antes y luego a 24 h antes, entonces el paciente recibe el
  recordatorio 1 y después el recordatorio 2 (salvo que haya reprogramado o
  cancelado), cada uno una sola vez.

**CA-2 — Confirmación de un toque** (RF-11)
- Dado un recordatorio recibido, cuando el paciente pulsa «Confirmo», entonces
  la cita pasa a Confirmada, recibe el agradecimiento y sigue recibiendo el
  recordatorio de 24 h.

**CA-3 — Reprogramar o cancelar avisa a la asistente** (RF-12, RF-13)
- Dado un recordatorio recibido, cuando el paciente pulsa «Reprogramar» o
  «Cancelar», entonces la cita pasa a Reprogramación solicitada o a Cancelada
  por paciente, según el botón, y aparece en «Requieren atención».

**CA-4 — Citas sin respuesta** (RF-15)
- Dado una cita no confirmada con recordatorio 2 enviado, cuando el paciente no
  responde, entonces la cita pasa a Sin confirmar y aparece destacada en
  «Requieren atención». Una cita ya Confirmada se mantiene Confirmada.

**CA-5 — Fallos visibles** (RF-16)
- Dado un fallo simulado en el envío, cuando se agotan los reintentos,
  entonces la cita se muestra como Error de envío en «Requieren atención».

**CA-6 — Calidad visual** (RF-17)
- Dado el panel y el simulador en modo demo, cuando se inspeccionan a 360 px
  de ancho, entonces no hay botones ni campos con el estilo por defecto del
  navegador, las fechas y horas se muestran en español legible, y cada estado
  se distingue por texto y color según la skill `brand-design`.

**CA-7 — Agenda simulada interactiva** (RF-3, RF-4, RF-6)
- Dado el modo demo, cuando la asistente crea una cita en la agenda simulada,
  entonces aparece en el panel y programa sus recordatorios; cuando la mueve de
  fecha u hora, se descartan los recordatorios de la fecha anterior y el ciclo
  se reinicia en Pendiente; cuando la cancela, no se reciben más recordatorios.

**CA-8 — Panel y agenda legibles a 360 px** (RF-17)
- Dado el modo demo a 360 px, cuando se abren el Panel y la Agenda, entonces no
  hay grilla de 7 columnas, cada cita es una fila a ancho completo, ningún
  nombre se parte por letras ni ningún estado se corta, y «Requieren atención»
  aparece antes que la agenda.

**CA-9 — Corregir teléfono** (RF-2, RF-18)
- Dado una cita «Sin teléfono» en modo demo, cuando la asistente agrega un
  teléfono válido y confirma que el paciente ya dio su consentimiento, entonces
  la cita pasa a Pendiente, sale de «Requieren atención» y se programan sus
  recordatorios. Si no hay consentimiento, queda «Sin consentimiento». En modo
  real, corregir el teléfono en Google Calendar produce el mismo efecto sin que
  la app escriba en el calendario.

### Criterios de finalización
- Los nueve criterios (CA-1 a CA-9) se cumplen en modo demo.
- Cada requisito funcional tiene al menos una prueba automática. En
  particular: RF-8 (sin consentimiento no se envía), RF-10 (sin duplicados),
  RF-14 (la última respuesta manda) y RF-18 (corregir teléfono).

## 7. Casos límite

- Cita agendada con menos de 24 h de anticipación → RF-6.
- Cita movida o cancelada en Google Calendar después de enviado un recordatorio
  → RF-3.
- Evento sin teléfono o con teléfono mal escrito → RF-2.
- Paciente que responde fuera de tiempo (después de la cita) → se ignora y se
  registra.
- Paciente con varias citas el mismo día → recibe un mensaje por cita.
- Recordatorio que cae de noche → RF-7.
- Paciente sin consentimiento → RF-8.
- Paciente que pide la baja → RF-9.
- Paciente que confirma y después cancela, o pulsa dos botones → RF-14.

## 8. Fuera de alcance de esta spec

Seguimiento de tratamientos de varias sesiones, lista de espera y reasignación
automática de espacios, proponer nuevos horarios al paciente, escribir o
modificar citas en Google Calendar, captura del consentimiento desde la
aplicación, métricas y reportes, facturación, expediente clínico, inventario.

## 9. Supuestos (revisar con la doctora)

- **S1 — Ventana de envío:** los mensajes se envían entre las 8:00 y las 20:00,
  hora del consultorio. Decisión confirmada.
- **S2 — Confirmar no detiene el recordatorio de 24 h:** el segundo aviso
  refuerza la cita y le sirve al paciente. Decisión confirmada.
- **S3 — Formato del teléfono:** línea `Tel:` en la descripción del evento, con
  código de país.
- **S4 — Consentimiento:** en el MVP es un dato previo por paciente; el sistema
  solo lo consulta. En la demo hay pacientes ficticios con y sin consentimiento.
- **S5 — Un solo consultorio, un solo calendario.**
- **S6 — Zona horaria única:** la del consultorio.

## 10. Métrica de éxito de negocio (posterior al despliegue real)

No se verifica con pruebas automáticas. Se mide con el consultorio funcionando:
- Inasistencias: de ~30 % a menos del 10 %.
- Tiempo semanal de la asistente dedicado a enviar recordatorios: cercano a cero.
- Periodo de medición y línea base: a definir con la doctora.

## 11. Dudas abiertas (no bloquean el MVP en modo demo)

- ¿En qué país opera el consultorio? Determina la normativa de datos
  aplicable (constitución, principio 11).
- ¿Cómo obtiene hoy el consultorio el consentimiento de los pacientes?
- ¿Cuántas citas por día maneja, aproximadamente?
- ¿El número del consultorio ya está en WhatsApp Business?
- ¿Cuál es el presupuesto mensual disponible?
