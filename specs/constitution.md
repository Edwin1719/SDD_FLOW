# Constitución — Recordatorios para consultorio dental

Principios innegociables. Toda spec, plan y tarea debe cumplirlos.

1. **Simplicidad primero**: se elige la solución más simple que cumpla la
   spec. Preferir servicios gestionados, costos predecibles y mantenimiento
   mínimo. Toda complejidad añadida se justifica por escrito en el plan.
2. **La spec manda**: ningún comportamiento se implementa si no está en la
   spec activa. Si falta una decisión, se detiene el trabajo y se pregunta.
   Si el resultado no cumple un criterio de aceptación, se corrige la spec
   antes que el prompt o el código.
3. **Google Calendar es la fuente de verdad de la agenda**: la aplicación se
   integra con él, no lo sustituye ni crea citas que lo contradigan. Usa solo
   los permisos mínimos necesarios.
4. **Privacidad por diseño**: solo se guarda lo estrictamente necesario
   (nombre, teléfono, tipo de tratamiento en términos generales, avance en
   sesiones y estado de consentimiento). Prohibido almacenar diagnósticos,
   notas clínicas, imágenes o cualquier dato de salud detallado. Los mensajes
   al paciente no incluyen detalles clínicos y los logs no incluyen datos
   personales.
5. **WhatsApp solo por canales oficiales y con consentimiento**: se usa la
   API oficial de WhatsApp Business con plantillas aprobadas. Sin
   consentimiento previo no se envía ningún mensaje; la baja del paciente se
   respeta de inmediato. Prohibida la automatización no oficial.
6. **Sin fallos silenciosos**: todo envío o sincronización que falle queda
   registrado y visible para la asistente. Los envíos son idempotentes:
   reintentar nunca duplica un mensaje al paciente.
7. **Lógica separada de integraciones**: las reglas de negocio no dependen
   directamente de WhatsApp ni de Google. Todo servicio externo va detrás de
   una interfaz, de modo que la lógica sea testeable sin ellos.
8. **Tests como puerta**: cada tarea termina con sus tests en verde.
   Prohibido avanzar con tests en rojo. Los tests automáticos nunca llaman a
   servicios reales (WhatsApp, Google).
9. **Operable por una persona no técnica**: la asistente debe usar el sistema
   desde el celular, sin capacitación larga y con acciones frecuentes en
   pocos toques.
10. **Alcance cerrado**: no se construye facturación, pagos, expediente
    clínico, historia clínica, odontograma ni inventario.
11. **Cumplimiento normativo**: se respeta la normativa de protección de
    datos personales aplicable al país del consultorio. Todo riesgo de
    cumplimiento detectado se reporta antes de implementar.
12. **Idioma**: código e identificadores en inglés; mensajes al usuario,
    mensajes al paciente y documentación en español.
13. **Ejecutable sin credenciales**: el proyecto debe poder ejecutarse y
    demostrarse de punta a punta con adaptadores simulados (WhatsApp, Google
    Calendar) y datos ficticios. Los servicios reales se activan solo por
    configuración. El repositorio nunca contiene credenciales ni datos reales
    de pacientes.
