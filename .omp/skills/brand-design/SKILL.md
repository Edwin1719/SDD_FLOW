---
name: brand-design
description: Identidad visual y de voz del Consultorio Dra. Laura (panel de la asistente y mensajes a pacientes para recordatorios y confirmación de citas). Úsala siempre que crees o cambies cualquier pantalla, plantilla HTML, CSS, componente, texto de interfaz, mensaje de error o mensaje al paciente de esta aplicación, incluso si solo piden "una pantalla sencilla", "un botón" o "arreglar un estilo". Define colores, tipografía, estados de la cita, composición, accesibilidad y tono.
---

# Marca — Consultorio Dra. Laura

Esta skill define **cómo se ve y cómo suena** la aplicación. Qué se muestra y qué dice cada mensaje lo define `spec.md` (secciones 4.3 y 4.4). Si algo de aquí choca con la spec, gana la spec: avisa del conflicto y no lo resuelvas por tu cuenta.

## Esencia

**Serena, clara y cercana.** La asistente consulta el panel en el celular, con prisa, entre pacientes; el paciente recibe un mensaje breve de un consultorio de confianza. Por eso la interfaz prioriza leer de un vistazo, sin adornos, y la voz es la de una persona amable que va al grano.

Dos elementos con identidad: el **logo de diente** (marca) y el **color de estado** de cada cita (función). Todo lo demás es silencioso.

## Cabecera y logo

- **Logo de diente**: SVG de línea, trazo uniforme, sin relleno; no se usan fotos ni ilustraciones.
- **Barra superior** en todas las pantallas: fondo `--superficie` (blanco), borde inferior `--borde`, logo de diente en `--acento` y nombre **«Consultorio de la Dra. Laura» en `--tinta`**, alineado a la izquierda. A la derecha, el badge «Demo · datos ficticios» con fondo `--acento` y texto blanco (contraste 4.5:1 o mayor).
- En celular la barra superior es compacta y el nombre puede ocupar dos líneas; no se usa una cabecera azul de altura completa.
- En escritorio la marca vive en la barra superior, no en una barra lateral.

## Navegación

Tres vistas: **Panel** (`/`), **Agenda** (`/agenda`) y **Simulador** (`/sim`), enlazadas con navegación fija:

- **Escritorio (≥768 px):** barra superior blanca con logo a la izquierda y los tres ítems con ícono y etiqueta al centro/derecha. El ítem activo se marca con texto `--acento` y un subrayado de 2 px. No hay barra lateral.
- **Celular (<768 px):** barra superior compacta con logo y badge; barra inferior fija con tres pestañas (ícono + etiqueta). La activa en `--acento`, las inactivas en `--pizarra`. No se usa menú hamburguesa.
- Íconos de línea simples: cuadrícula (Panel), calendario (Agenda), reproducir (Simulador).
- El contenido usa el ancho disponible en escritorio (máximo ~1200 px), no una columna de 640 px con media pantalla vacía.

## Color

Usa siempre las variables del bloque CSS de abajo; nunca escribas un hexadecimal en una plantilla.

| Variable | Uso |
|---|---|
| `--fondo` | Fondo de la página |
| `--superficie` | Tarjetas y filas |
| `--tinta` | Texto principal |
| `--pizarra` | Texto secundario |
| `--acento` | Azul corporativo: botones, enlaces, foco, logo |
| `--borde` | Divisores y bordes de superficies |

Estas son todas las variables de la marca; copia este bloque tal cual a la hoja de estilos de la aplicación (es la fuente de verdad de los valores):

```css
:root {
  /* Color base */
  --fondo: #F8FAFC;
  --superficie: #FFFFFF;
  --tinta: #0F172A;
  --pizarra: #64748B;
  --acento: #2563EB;
  --borde: #E2E8F0;

  /* Tonos de estado (texto y fondo; contraste 4.5:1 o mayor) */
  --neutro-texto: #475569;  --neutro-fondo: #F1F5F9;
  --exito-texto: #15803D;   --exito-fondo: #DCFCE7;
  --atencion-texto: #B45309; --atencion-fondo: #FEF3C7;
  --peligro-texto: #B91C1C; --peligro-fondo: #FEE2E2;
  --morado-texto: #7E22CE;  --morado-fondo: #F3E8FF;

  /* Tipografía */
  --fuente: "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --t-14: 0.875rem; --t-16: 1rem; --t-18: 1.125rem;
  --t-20: 1.25rem;  --t-24: 1.5rem; --t-30: 1.875rem;

  /* Espacio (base 4 px) y forma */
  --e-1: 4px; --e-2: 8px; --e-3: 12px; --e-4: 16px; --e-6: 24px; --e-8: 32px;
  --radio-control: 8px;
  --radio-superficie: 14px;
  --objetivo-tactil: 44px;
}
```

Reglas: un solo acento (azul); sin degradados; sin sombras (la separación se logra con bordes `--borde` y cambios de fondo); sin modo oscuro en el MVP. Los contrastes de texto están verificados; si añades un color, comprueba que cumple 4.5:1.

## Estados de la cita

Los nombres son exactamente los de `spec.md` 4.2. **El estado se comunica siempre con texto y símbolo, nunca solo con color** (RF-17).

| Estado | Tono | Símbolo |
|---|---|---|
| Pendiente | neutro | ○ |
| Recordatorio enviado | neutro | ◐ |
| Confirmada | éxito (verde) | ✓ |
| Reprogramación solicitada | atención (ámbar) | ↻ |
| Cancelada por paciente | morado | ✕ |
| Sin confirmar | atención (ámbar) | ? |
| Error de envío | peligro (rojo) | ! |
| Sin teléfono | atención (ámbar) | ! |
| Sin consentimiento | neutro | ⊘ |

Cada tono usa sus variables `--{tono}-texto` y `--{tono}-fondo`. Dibuja los símbolos como SVG en línea con el mismo significado.

## Tipografía

Una sola familia: **Atkinson Hyperlegible** (400 y 700), pensada para máxima legibilidad. Cárgala vía Google Fonts con `font-display: swap` y verifica su disponibilidad al implementar; el panel debe verse correcto con la pila de respaldo `system-ui` si no carga. Base de 16 px, escala 14 / 16 / 18 / 20 / 24 / 30. Horas con cifras tabulares (`font-variant-numeric: tabular-nums`). Texto en minúscula normal (sin mayúsculas sostenidas), líneas de menos de 70 caracteres. Excepción puntual: las etiquetas de las tarjetas de resumen («REQUIEREN ATENCIÓN», «CITAS HOY») pueden ir en mayúsculas pequeñas.

## Forma y espacio

Base de 4 px (4, 8, 12, 16, 24, 32). Dos radios con jerarquía: 8 px en controles y etiquetas, 14 px en superficies. Sin sombras; la separación se logra con bordes `--borde` y cambios de fondo.

## Composición del panel

- Una columna en celular y hasta dos columnas en escritorio, pensada primero para 360 px.
- **Barra superior** con logo, nombre, navegación y badge (ver Navegación).
- **Título** `h1` «Panel» y la fecha del día.
- **Resumen** (arriba): tres tarjetas compactas — «Citas hoy», «Atención» y «Confirmadas». Etiqueta de 12 px como mínimo, número grande y una línea secundaria.
- **Requieren atención** inmediatamente debajo del resumen: filas con barra de 4 px en el tono del estado, hora, nombre, estado y una acción concreta. No es una lista pasiva: «Agregar teléfono», «Ver en agenda» o «Corregir en Google Calendar».
- **Agenda de hoy** debajo: filas de lista, no una grilla de 7 columnas. Si hoy no hay citas, muestra las próximas citas con su fecha.
- **«Así funciona»** al final y compacto: recorrido guiado con enlaces a cada vista.
- Cada cita es una **fila de lista**: hora (grande, tabular) · nombre y teléfono · etiqueta de estado · acciones. En pantallas estrechas el estado y las acciones bajan bajo el nombre, pero nunca se parten letras ni se corta el texto.
- En escritorio, el Panel puede mostrar la agenda a la izquierda y el resumen/atención a la derecha; en celular va en una sola columna y «Requieren atención» aparece antes que la agenda.
- No inventes acciones ni pantallas que no estén en la spec: en modo real la asistente edita o reprograma en Google Calendar; en modo demo la agenda simulada sí permite editar.
- En modo demo, badge fijo «Demo · datos ficticios».

## Accesibilidad

Objetivos táctiles de 44 px como mínimo; foco visible con el anillo de `--acento`; respeta `prefers-reduced-motion` (sin animaciones no pedidas por una acción); sin desbordamiento horizontal a 360 px; el estado nunca depende solo del color. Los nombres y estados no se parten por letras: si una fila no cabe, el contenido baja de línea. La grilla de 7 columnas no se usa en celular.

## Voz y tono

Tuteo, frases cortas, verbos simples, sin jerga técnica. Nombra las cosas como las entiende la asistente: «calendario», no «sincronización»; «recordatorio», no «job».

| En lugar de | Escribe |
|---|---|
| «Error 500» | «No pudimos leer el calendario. Tus citas siguen guardadas; reintenta en unos minutos.» |
| «Falló el envío» | «No se pudo enviar el recordatorio. Avísale al paciente por teléfono.» |
| «Sin datos» | «Hoy no hay citas.» |
| «Enviar» | «Confirmar» (el botón dice lo que hace) |

- Los errores explican qué pasó y qué hacer; no se disculpan ni dramatizan.
- Los estados vacíos invitan a actuar o informan con calma.
- Una acción conserva el mismo nombre en todo el flujo.

**Mensajes al paciente** (cuando redactes textos nuevos; los de la spec 4.3 no se alteran): neutros, sin ningún detalle clínico, sin emojis, como máximo una exclamación, con el nombre y la fecha completos, firmados como «Consultorio de la Dra. Laura».

## Lo que se evita

Fondo crema con acento terracota, negro casi puro con un acento neón, tarjetas idénticas con sombra gris, etiquetas en mayúsculas sobre cada título, subrayar una sola palabra de un titular, flechas «→» al final de botones, degradados decorativos y una paleta de arcoíris para los estados (máximo un tono por significado). Son los valores por defecto de cualquier interfaz generada y esta marca no los usa.

## Antes de dar una pantalla por terminada

1. No hay hexadecimales sueltos: todo sale de las variables de la marca.
2. Cada estado tiene texto, símbolo y tono correctos.
3. Se ve bien a 360 px, sin desplazamiento horizontal.
4. Los textos cumplen la sección de voz y coinciden con la spec.
5. El foco con teclado es visible en cada control.
6. La barra superior muestra el logo de diente y el nombre alineado a la izquierda.
7. No hay grilla de 7 columnas en celular: cada cita es una fila legible.
8. Los textos sobre fondos de color cumplen 4.5:1, incluido el badge de demo.
