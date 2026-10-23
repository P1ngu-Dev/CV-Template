# Flujo de postulación

Guía operativa para crear, adaptar y enviar una postulación sin romper el CV
maestro ni inventar experiencia.

## Principios

1. **Una fuente de verdad.** `main/cv.yaml` contiene tu historia completa.
2. **Una copia por postulación.** `applications/<carpeta>/cv.yaml` se deriva del
   maestro y se adapta; el maestro no se toca.
3. **Todo verificable.** Si un logro no está en el CV maestro ni lo entregó el
   usuario, no se agrega.
4. **Todo registrado.** Cada postulación termina con estado y fecha en
   `application_log.md`.

## Antes de empezar

```bash
python3 scripts/cv.py setup
python3 scripts/cv.py init --name "Tu Nombre"
python3 scripts/cv.py check
```

Edita `main/cv.yaml` con tu información real. Verifica que compile antes de
crear cualquier postulación.

## Paso 0 — ¿Actualizar el maestro?

Actualiza `main/cv.yaml` solo cuando tengas **contenido nuevo permanente**:
nuevo trabajo, proyecto, certificación, habilidad o logro. No lo modifiques para
"hacer match" con una oferta puntual; eso va en la copia de la postulación.

Después de actualizarlo:

```bash
python3 scripts/cv.py check
```

## Paso 1 — Crear la carpeta

```bash
python3 scripts/cv.py new "Banco BICE" "Práctica Informática" \
  --url "https://www.linkedin.com/jobs/view/123456" \
  --job-file ~/Descargas/oferta-bice.md
```

Si no tienes la oferta en un archivo, créala sin `--job-file` y pégala después
en `job_description.md`. La carpeta se nombra `YYYY-MM-empresa-rol` y **no debe
renombrarse** después de crear el registro.

## Paso 2 — Guardar la oferta

En `job_description.md`:

- Texto completo o resumen fiel (no interpretado).
- Link estable (no un redirect temporal).
- Fecha de captura.
- Si la oferta se cierra, conserva el texto: sirve para entrevistas.

## Paso 3 — Analizar

Completa `analysis.md`:

- **Veredicto rápido**: ¿vale la pena postular? (sí / sí con reservas / no).
- **Keywords clave**: tecnologías, metodologías y palabras exactas de la oferta.
- **Requisitos obligatorios y deseables**, separados.
- **Match con el CV actual**: qué evidencia existe para cada requisito.
- **Cambios sugeridos**: qué mover, reescribir o recortar.
- **Brechas y riesgos**: lo que no puedes demostrar y cómo mitigarlo.
- **Estrategia**: canal, contacto, carta o mensaje, timing.

Con un agente, usa la skill `job-description-analyzer`. No le pidas que invente
experiencia para cubrir brechas.

## Paso 4 — Adaptar el CV

Edita solo `applications/<carpeta>/cv.yaml`.

| Sí puedes | No puedes |
| --- | --- |
| Reordenar secciones y bullets | Agregar empresas o cargos |
| Reformular con las keywords de la oferta | Cambiar fechas o títulos |
| Recortar contenido irrelevante | Inventar métricas |
| Cambiar el `headline` y el resumen | Inventar certificaciones |
| Ajustar el orden de habilidades | Declarar idiomas no reales |

Reglas de contenido:

- Máximo 1 página para prácticas/junior; 2 para senior.
- Cada bullet: verbo de acción + qué hiciste + resultado (si existe el dato).
- Keywords integradas en frases con contexto, no en listas sueltas.
- Fechas consistentes (`YYYY-MM` o `YYYY`), sin mezclar formatos.
- Sin emojis, sin fotos salvo que la oferta lo pida.

Con un agente: `resume-tailor` para la adaptación y `resume-bullet-writer` para
los bullets.

## Paso 5 — Renderizar y revisar

```bash
python3 scripts/cv.py render <carpeta>
```

Revisa en `outputs/`:

- [ ] El PDF abre y tiene el número de páginas esperado.
- [ ] No hay texto cortado ni secciones huérfanas.
- [ ] Los links funcionan (correo, LinkedIn, GitHub).
- [ ] El nombre y el headline coinciden con la oferta.
- [ ] No quedaron placeholders (`{{...}}`) ni texto de ejemplo.
- [ ] Ortografía y tildes correctas.

## Paso 6 — ATS

Usa `resume-ats-optimizer` o revisa manualmente:

- [ ] El PDF tiene texto seleccionable (no es imagen).
- [ ] Una sola columna lógica y encabezados estándar.
- [ ] Las keywords aparecen tal como las pide la oferta.
- [ ] Sin tablas, cajas de texto ni gráficos que oculten contenido.
- [ ] El nombre del archivo es legible (`Nombre_Apellido_CV.pdf`).

Ajusta el YAML y vuelve a renderizar. Repite hasta que el PDF y el ATS coincidan.

## Paso 7 — Carta o mensaje (opcional)

En `cover_letter.md`, solo si la oferta lo pide o si escribirás al reclutador:

- Máximo 250 palabras si es correo; 1 página si es carta.
- Menciona 2 logros concretos y verificables del CV.
- Conecta esos logros con 2 requisitos explícitos de la oferta.
- Nada de plantillas genéricas: adapta empresa, rol y canal.

## Paso 8 — Enviar y registrar

```bash
python3 scripts/cv.py set-status <carpeta> applied --sent-date 2026-02-03
```

Estados recomendados:

| Estado | Cuándo |
| --- | --- |
| `draft` | Carpeta creada, sin enviar |
| `applied` | Enviada |
| `screening` | Contacto inicial o prueba técnica |
| `interview` | Entrevistas en curso |
| `offer` | Oferta recibida |
| `rejected` | Rechazo o cierre |
| `withdrawn` | Retiraste la postulación |

Registra también en `application_log.md`: contacto, canal, respuestas y
siguientes pasos con fecha.

## Checklist de cierre

```bash
python3 scripts/cv.py check
python3 scripts/cv.py list
```

- [ ] `check` pasa sin errores.
- [ ] `application_log.md` tiene estado y fecha de envío.
- [ ] `outputs/` no se commiteó (está en `.gitignore`).
- [ ] Si el repo es público, no hay datos personales en el commit.

## Errores comunes

| Problema | Causa / solución |
| --- | --- |
| El render falla por YAML | Falta `area` en educación o un campo obligatorio; lee el error de RenderCV |
| El PDF tiene 2 páginas y quieres 1 | Recorta bullets antiguos, no reduzcas la fuente |
| El ATS no lee el PDF | El tema genera columnas; prueba `engineeringresumes` o `sb2nov` |
| Cambiaste el maestro sin querer | `git diff main/cv.yaml` y revierte con `git checkout -- main/cv.yaml` |
| Se mezclaron dos ofertas | Crea una carpeta nueva; no reutilices la existente |
