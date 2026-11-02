# ICP — Consultorio dental

**Proyecto:** Recordatorios para consultorio dental
**Tipo de documento:** documento de negocio y mercado. **No es una spec de producto.**
**Estado:** borrador para validar con la doctora y el equipo.
**Fecha:** 2026-11-02
**Base:** definición del problema de la Tarea 1 ([spec 001](specs/001-recordatorios-confirmacion/spec.md), [README](README.md)).
**Relación con el producto:** este documento define a quién le sirve el negocio; las specs definen cómo se comporta la app.

> **Regla:** lo que no viene de la Tarea 1 es una hipótesis marcada como tal. No se inventan precios, límites ni políticas de WhatsApp o Google; eso se verifica en la documentación oficial.

## 1. Resumen

**ICP en una frase:** consultorio dental privado e independiente, de una sola sede, con 1–3 odontólogos y 1–2 asistentes, entre 12 y 25 citas al día, que usa Google Calendar como agenda y WhatsApp como canal con pacientes, tiene una inasistencia superior al 15 % y no cuenta con equipo de TI.

**Quién compra:** la dueña-odontóloga. **Quién usa:** la asistente. **Quién responde:** el paciente.

## 2. Industria

| Dimensión | Definición |
|---|---|
| Sector | Salud odontológica ambulatoria |
| Subsector | Consultorio privado e independiente de odontología general y especialidades |
| Servicios típicos | Consulta, limpieza, control, tratamientos restaurativos y seguimiento |
| Tamaño | 1 sede, 1–3 odontólogos, 2–4 sillones, 1–2 asistentes |
| Modelo de atención | Citas programadas, pacientes recurrentes y tratamientos de varias sesiones |
| Pago | Directo del paciente o planes prepagados; validar con la doctora |
| Fuera de la industria objetivo | Hospitales, clínicas grandes, cadenas con call center, consultorios con EHR/CRM propio |

**Contexto regulatorio:** se manejan datos personales y de salud. El producto solo debe guardar datos mínimos (nombre, teléfono, estado, consentimiento); nunca diagnósticos, notas clínicas ni imágenes.

## 3. Datos geográficos

| Dimensión | Hipótesis inicial |
|---|---|
| País | Colombia primero; LatAm hispanohablante después |
| Ciudades | Bogotá, Medellín, Cali, Barranquilla (a validar) |
| Zona | Urbana, con pacientes en un radio local |
| Idioma | Español |
| Moneda | COP; el precio se define en otra etapa |
| Teléfono | Prefijo +57, celular y WhatsApp |
| Zona horaria | America/Bogota |
| Canal de contacto | WhatsApp y llamadas locales |
| Cobertura | Una sede y una agenda; no multisitio en el MVP |

No se usan tamaños de mercado ni cifras de penetración sin fuente. La geografía es una hipótesis de lanzamiento, no un dato verificado.

## 4. Datos tecnográficos

| Dimensión | Perfil del ICP |
|---|---|
| Agenda | Google Calendar compartido entre dueña y asistente |
| Canal con pacientes | WhatsApp del consultorio, Business o personal |
| Dispositivo | Celular; la asistente lo usa como herramienta principal |
| Sistemas | Sin CRM ni EHR; a lo sumo Excel para cobros o reportes |
| Equipo de TI | No existe; nadie configura APIs ni servidores |
| Internet | Estable en el consultorio; no se asume fibra dedicada |
| Madurez digital | Media-baja: usa herramientas cotidianas, no integraciones |
| Herramientas de apoyo | Instagram, Google Maps, teléfono, WhatsApp Web |
| Lo que no quiere | Instalar software pesado, cambiar de calendario o migrar historia clínica |

**Implicación:** el producto debe funcionar en el celular, en español, sin instalación y sin pedir integraciones.

## 5. Puntos de dolor operacionales

| Dolor | Señal en el consultorio | Impacto | Workaround actual |
|---|---|---|---|
| Inasistencia alta | Silla vacía, paciente que no contesta | Ingreso perdido y agenda rota | Llamar o escribir a mano |
| Recordatorios manuales | La asistente copia y pega mensajes | 45–90 min/día y errores | WhatsApp uno por uno |
| Cancelaciones tardías | Aviso el mismo día | Espacio que no se recupera | Llamar a pacientes de memoria |
| Falta de seguimiento | No se sabe quién confirmó | La asistente persigue respuestas | Revisar chats y agenda |
| Teléfonos mal escritos o ausentes | «Sin teléfono» en la agenda | No se puede contactar | Llamar o buscar en otro lado |
| Sobrecarga de la asistente | Mensajes a toda hora | Estrés y errores | Trabajo fuera de horario |
| Abandono de tratamientos | Paciente no vuelve a la siguiente sesión | Menor ingreso y peor resultado | Recordatorio manual, si se acuerda |
| Poca visibilidad de la dueña | No sabe qué citas están en riesgo | Decide tarde | Preguntar a la asistente |

Los tres primeros son el núcleo del MVP. El abandono de tratamientos es una oportunidad de una spec posterior.

## 6. Disparadores de compra

| Disparador | Señal | Por qué compra ahora | Urgencia |
|---|---|---|---|
| Pico de inasistencias | Varias sillas vacías en la semana | Siente la pérdida de ingresos | Alta |
| Crecimiento | Nuevo odontólogo, sillón u horario | Necesita ordenar la agenda sin más personal | Alta |
| Sobrecarga de la asistente | Se queda tarde enviando mensajes | Quiere recuperar tiempo y evitar errores | Alta |
| Cambio de asistente | Se va la persona que «se sabía» la agenda | Necesita que el proceso no dependa de una persona | Media-alta |
| Apertura de consultorio | Montaje de una sede nueva | Quiere empezar con un proceso profesional | Alta |
| Mala experiencia del paciente | Quejas por esperas o citas perdidas | Cuida la reputación | Media |
| Temporada alta | Más demanda en ciertos meses | No puede fallar en la operación | Media |
| Referido o competencia | Un colega le mostró una herramienta | Ve que es posible | Media |
| Proceso manual fallido | Olvidó enviar recordatorios | Quiere una red de seguridad | Alta |

**Diferencia clave:** el dolor es crónico; el disparador es el evento que hace que la dueña actúe.

## 7. Dónde encontrarlo

| Canal | Cómo llegar | Por qué funciona | Prioridad |
|---|---|---|---|
| Referidos de odontólogos | Preguntar a clientes por colegas | Confianza entre pares | Alta |
| Proveedores y laboratorios dentales | Alianzas con representantes | Ya visitan consultorios y son de confianza | Alta |
| Asociaciones y grupos dentales | Charlas, eventos, grupos locales | Acceso concentrado al ICP | Alta |
| Instagram y Facebook | Contenido de gestión de consultorio | La dueña consume contenido local | Media |
| Google Maps | Búsqueda de consultorios por zona | Intención local y datos de contacto | Media |
| WhatsApp y grupos de colegas | Referidos y mensajes directos | Canal natural del ICP | Alta |
| Congresos y ferias dentales | Presencia o alianzas | Contacto cara a cara | Media |
| Directorios y guías locales | Listados de clínicas | Descubrimiento | Baja |
| Venta directa del fundador | 50 consultorios objetivo | Aprendizaje y cierre rápido | Alta |

## 8. Perfil de compra y uso

| Persona | Rol | Qué le importa | Frase |
|---|---|---|---|
| Dra. Laura, 42 | Dueña y compradora | Sillas llenas, ingresos, no complicarse | «Quiero que las sillas no se me queden vacías.» |
| Marcela, 29 | Asistente y usuaria principal | Menos trabajo manual, claridad | «Quiero dejar de copiar mensajes.» |
| Andrés, 34 | Paciente | Confirmar con un toque, sin llamadas | «Si es un toque, lo hago.» |

**La compra se gana en la dueña; la adopción se gana en la asistente.** Si Marcela no lo usa, el producto no funciona aunque la doctora lo compre.

## 9. Debe cumplir / No es ICP

**Debe cumplir:**

- Consultorio privado e independiente, una sede.
- 1–3 odontólogos y al menos una asistente.
- Google Calendar como agenda real.
- WhatsApp como canal con pacientes.
- 10–30 citas al día.
- Inasistencia percibida ≥ 15 % o dolor operativo claro.
- Dueña o gerente con capacidad de decisión.
- Español y operación en Colombia/LatAm.

**No es ICP:**

- Hospital, clínica grande o cadena con call center.
- Consultorio que exige EHR/CRM, historia clínica u odontograma integrado.
- Agenda en papel, Excel o software cerrado sin Google Calendar.
- Consultorio sin WhatsApp o fuera de español/LatAm.
- Expectativa de producto gratuito sin presupuesto.
- Necesidad de datos clínicos o imágenes.

## 10. Supuestos a validar

| Supuesto | Confianza | Cómo se valida | Criterio |
|---|---|---|---|
| Usan Google Calendar como agenda real | Media | Entrevista y pantalla compartida | 7/10 |
| WhatsApp es el canal principal | Alta | Entrevista | 8/10 |
| Inasistencia > 15 % | Media | Últimas 4 semanas | 6/10 |
| La asistente dedica > 45 min/día | Media | Observación de una mañana | 6/10 |
| El consentimiento está disponible | Baja | Entrevista | 6/10 |

## 11. Encaje de negocio

- **Propuesta de valor para la dueña:** menos sillas vacías y menos tiempo manual, sin cambiar Google Calendar.
- **Propuesta para la asistente:** una sola pantalla para saber a quién escribir y qué espacio ofrecer.
- **Propuesta para el paciente:** confirmar o cambiar la cita con un toque.
- **Modelo de ingreso (hipótesis):** suscripción mensual por consultorio; precio por definir con la doctora. No se asume precio por mensaje ni límite de WhatsApp sin verificarlo.
- **Ventaja defendible:** flujo pegrado a Google Calendar y WhatsApp, confianza local y datos de espacios recuperados; no la IA.
- **Costo de cambio:** bajo para empezar (demo y onboarding), alto cuando la agenda y la lista de espera ya viven en el producto.

## 12. Cómo se usa este documento

- **No es una spec:** no define requisitos, estados ni comportamiento de la app.
- **Alimenta las specs:** prioriza qué construir (recordatorios, recuperación de espacios, tratamientos).
- **Alimenta el lanzamiento:** define a quién buscar, con qué mensaje y por dónde.
- **Alimenta la calificación:** permite descartar consultorios que no cumplen el must-have.

**Siguiente paso:** validar este ICP con 10–15 entrevistas y ajustar industria, ciudades, dolores y disparadores antes de escribir el plan de lanzamiento.
