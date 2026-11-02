# Paso 1 — ICP y user persona

**Proyecto:** Recordatorios para consultorio dental
**Estado:** versión ejecutiva para validar. No es un documento aprobado todavía.
**Fecha:** 2026-11-02
**Base:** definición del problema de la Tarea 1 ([`spec.md`](../001-recordatorios-confirmacion/spec.md), [`README.md`](../../README.md)).

> **Regla del documento:** un ICP no es un plan de lanzamiento. Aquí solo se define a quién le sirve el producto, quién decide, quién lo usa y qué consultorios quedan fuera. Canales, landing, precios, onboarding y métricas van en el Paso 2.

## 1. ICP en una frase

> **Consultorio dental privado e independiente, de una sola sede, con 1–3 odontólogos y 1–2 asistentes, entre 12 y 25 citas al día, que usa Google Calendar como agenda y WhatsApp como canal con pacientes, tiene una inasistencia superior al 15 % y no tiene equipo de TI.**

Colombia o LatAm hispanohablante. La dueña-odontóloga decide; la asistente usa el producto todos los días.

**Debe cumplir:**

- Consultorio privado e independiente, una sede.
- 1–3 odontólogos y al menos una asistente.
- Google Calendar como agenda real.
- WhatsApp como canal con pacientes.
- 10–30 citas al día.
- Inasistencia percibida ≥ 15 % o dolor claro por recordatorios manuales.

**No es ICP:**

- Hospital, clínica grande o cadena con call center.
- Consultorio que exige EHR/CRM, historia clínica u odontograma integrado.
- Agenda en papel, Excel o software cerrado sin Google Calendar.
- Consultorio sin WhatsApp o fuera de español/LatAm.

## 2. Compradora — Dra. Laura

| Campo | Dato (hipótesis ilustrativa) |
|---|---|
| Rol | Odontóloga fundadora y dueña |
| Consultorio | 1 sede, 2 sillones, 1 asistente |
| Experiencia | 12 años |
| Volumen | ~18 citas/día; inasistencia ~30 % |
| Herramientas | Google Calendar, WhatsApp, celular; sin CRM/EHR |
| Decisión | Decide y paga; la asistente influye |

**Objetivos:** reducir ausencias, recuperar el tiempo de la asistente, crecer sin contratar otra persona.

**Dolores:** sillas vacías, mañanas copiando recordatorios, cancelaciones de última hora que no se recuperan.

**Frase:** «Yo no quiero otro sistema. Quiero que las sillas no se me queden vacías.»

**Objeciones clave:** «¿me reemplaza el calendario?», «¿es oficial?», «¿es caro?», «¿quién lo configura?». Las respuestas van en el Paso 2.

## 3. Usuaria principal — Marcela, la asistente

| Campo | Dato (hipótesis ilustrativa) |
|---|---|
| Rol | Asistente dental / recepción |
| Edad | 29 años |
| Volumen | 18–25 citas/día |
| Herramientas | Google Calendar, WhatsApp Web, celular |
| Tiempo en recordatorios | 45–90 minutos/día, uno por uno |
| Tecnología | Aprende haciendo; no configura APIs |

**Dolores:** copiar y pegar mensajes, respuestas dispersas entre WhatsApp y la agenda, no saber a quién seguir.

**Ganancias:** recordatorios automáticos, una sola pantalla con «quién necesita atención», menos llamadas y mensajes repetidos.

**Riesgo de adopción:** sentir que la herramienta la reemplaza o que es «otro sistema» que le quita tiempo. Si Marcela no la usa, el producto no funciona aunque la doctora lo compre.

**Frase:** «Quiero dejar de copiar mensajes y saber a quién llamar.»

## 4. Paciente — Andrés (secundario)

- 34 años, profesional urbano, agenda por WhatsApp.
- Quiere confirmar, reprogramar o cancelar con **un toque**.
- No quiere llamadas, mensajes largos ni detalles clínicos.
- Si pide la baja, se respeta de inmediato.

No compra ni decide, pero sin su respuesta el producto no sirve.

## 5. Supuestos a validar

Todo lo que no viene de la Tarea 1 es hipótesis. Estos son los cinco supuestos que más cambian el lanzamiento:

| Supuesto | Confianza | Cómo se valida | Criterio |
|---|---|---|---|
| Usan Google Calendar como agenda real | Media | Entrevista y pantalla compartida | 7/10 |
| WhatsApp es el canal principal | Alta | Entrevista | 8/10 |
| Inasistencia > 15 % | Media | Últimas 4 semanas | 6/10 |
| La asistente dedica > 45 min/día | Media | Observación de una mañana | 6/10 |
| El consentimiento está disponible | Baja | Entrevista | 6/10 |

## 6. Implicaciones para el lanzamiento

**Mensaje por persona:**

- **Dra. Laura:** «Menos sillas vacías, sin contratar a nadie más.»
- **Marcela:** «El panel te dice a quién escribir; tú no persigues confirmaciones.»
- **Andrés:** «Confirma tu cita con un toque.»

**Preguntas de calificación:**

1. ¿Usan Google Calendar como agenda?
2. ¿Cuántas citas ven al día y cuántas fallan?
3. ¿Quién envía los recordatorios y cuánto tiempo le toma?
4. ¿Usan WhatsApp con los pacientes?
5. ¿Quién decide probar una herramienta nueva?

**No afirmar todavía:** precios o límites de WhatsApp/Google sin verificar; que la app reemplaza el calendario; que elimina el 100 % de las inasistencias; que guarda datos clínicos.

## 7. Qué sigue

Con este ICP validado, el **Paso 2** define propuesta de valor, canales, landing, guion de ventas, onboarding y métricas. El detalle largo que ya escribimos se mueve allí como material de apoyo.
