# AGENTS.md — Recordatorios para consultorio dental

## Proyecto
Aplicación web ligera para un consultorio dental pequeño que reduce las
inasistencias con recordatorios por WhatsApp y confirmación de un toque.
Se integra con Google Calendar (fuente de verdad de la agenda; no la reemplaza).

## Documentos (léelos antes de tocar código)
1. `specs/constitution.md`: principios innegociables.
2. `specs/001-recordatorios-confirmacion/spec.md`: qué se construye (un solo feature).
3. `specs/001-recordatorios-confirmacion/plan.md`: cómo se construye (stack y estructura).
4. `specs/001-recordatorios-confirmacion/tasks.md`: qué toca ahora.
5. `.omp/skills/brand-design/SKILL.md`: identidad visual y tono. Aplícala en toda interfaz y mensaje.

Flujo: constitución → spec → plan → tareas → código.

## Comandos
- Instalar: `python -m venv .venv`, activar el entorno y `pip install -r requirements.txt`
- Ejecutar (modo demo por defecto): `uvicorn app.main:app --reload`
- Pruebas: `pytest -q`

## Estilo
- Python 3.12+, anotaciones de tipos en funciones públicas.
- El dominio (`app/domain/`) no hace E/S: no importa `fastapi`, `sqlite3` ni `httpx`.
- Todo servicio externo (WhatsApp, Google, reloj) pasa por un puerto de `app/ports/`.
- Identificadores en inglés; textos en español solo en `app/texts_es.py`.
- Interfaz: aplica la skill `brand-design`.

## Reglas
- Si falta una decisión, detente y pregunta; no adivines.
- No avances de etapa sin aprobación del usuario.
- Si el resultado no cumple un criterio de aceptación, propón primero la
  corrección de la spec y espera aprobación; no parchees el código ni
  ajustes el prompt para esquivarlo.
- No añadas dependencias ni cambies contratos o modelo de datos sin
  actualizar antes la spec o el plan.
- No inventes costos, límites ni políticas de WhatsApp o Google: verifícalos
  en la documentación oficial y di cuándo no estés seguro.
- Pide permiso antes de migraciones, despliegues o cambios de credenciales.
- Nunca imprimas ni subas secretos.
- No modifiques `constitution.md` ni documentos aprobados sin petición explícita.

## Al terminar cualquier tarea
- Ejecuta las pruebas y confirma en tu respuesta que pasan.
- Marca la tarea en `tasks.md`.
