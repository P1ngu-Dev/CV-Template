# AGENTS.md

Instrucciones canónicas para agentes de IA que trabajen en este repositorio.
Este archivo aplica a todo el proyecto. Si algo aquí contradice a un archivo de
un agente específico, manda este archivo.

## Qué es este repo

Workspace **CV-as-code**: el CV se escribe en YAML y RenderCV lo convierte en
PDF/Markdown/HTML. `main/cv.yaml` es el CV maestro. Cada postulación real vive
en `applications/<YYYY-MM-empresa-rol>/` con su propia copia adaptada.

## Reglas duras

1. **No inventes experiencia.** No agregues empresas, cargos, fechas, títulos,
   certificaciones ni métricas que no existan en `main/cv.yaml` o que el usuario
   no haya entregado explícitamente. Reformular, reordenar y recortar sí;
   inventar no.
2. **El maestro no se toca al adaptar.** Para una postulación edita
   `applications/<carpeta>/cv.yaml`. Solo modifica `main/cv.yaml` si el usuario
   pide actualizar su CV maestro.
3. **Una postulación = una carpeta.** No mezcles archivos de distintas empresas.
4. **`outputs/` es generado.** No edites PDF/HTML/MD a mano; se regeneran con
   `cv.py render`.
5. **Valida antes de declarar "listo".** Ejecuta `cv.py check` (o la tool MCP
   `cv_check`) y muestra el resultado.
6. **No commitees datos personales en la plantilla pública.** Si el repo es un
   fork público, `main/cv.yaml` y `applications/` con datos reales no deben
   publicarse. Revisa `git status` antes de un commit.
7. **Idioma:** documentación y respuestas en español; el CV respeta el idioma de
   la oferta (por defecto español, locale `spanish`).

## Mapa del repo

```text
main/cv.yaml              CV maestro (fuente de verdad, no versionado en la plantilla)
main/example_cv.yaml      Ejemplo completo y válido para partir
applications/             Una carpeta por postulación real
  example/                Postulación de demostración completa
templates/                Plantillas con placeholders {{COMPANY}}, {{ROLE}}, ...
scripts/cv.py             CLI única (usar siempre esta)
scripts/cvlib.py          Núcleo compartido; no dupliques lógica en otro lado
mcp/cv_workspace_server.py Servidor MCP (stdio, sin dependencias)
docs/                     Flujo de postulación e integración con agentes
.agents/skills/           Fuente única de skills de CV (no editar a mano)
skills-lock.json          Lockfile canónico del CLI de skills
contexts/, portfolio/, linkedin/, references/
                          Material de apoyo (no lo usa el CLI)
archive/                  Material histórico; no es fuente de verdad
tools/                    Utilidades opcionales y aisladas (browser-agent-eval)
```

## Comandos canónicos

Usa `python3` en macOS/Linux y `python` en Windows. Nunca ejecutes `rendercv`
directamente: el CLI resuelve el ejecutable correcto (`.venv` o PATH).

```bash
python3 scripts/cv.py setup          # crea .venv, instala RenderCV y enlaza skills
python3 scripts/cv.py init --name "Nombre Apellido"
python3 scripts/cv.py new "Empresa" "Rol" --url "https://..." [--job-file oferta.md]
python3 scripts/cv.py render main
python3 scripts/cv.py render <carpeta-de-applications>
python3 scripts/cv.py check          # valida maestro + ejemplo + postulaciones
python3 scripts/cv.py list
python3 scripts/cv.py status
python3 scripts/cv.py doctor
python3 scripts/cv.py sync-skills
python3 scripts/cv.py set-status <carpeta> applied --sent-date 2026-02-01
```

Equivalentes con `make`: `make setup`, `make init NAME="..."`,
`make new COMPANY="..." ROLE="..." URL="..."`, `make render APP=...`,
`make check`, `make list`, `make doctor`.

Si `rendercv` no está disponible, no lo instales globalmente por tu cuenta:
indica al usuario que ejecute `python3 scripts/cv.py setup`.

## Flujo de una postulación

1. `cv.py new` (o `make new`) para crear la carpeta y los archivos.
2. Guardar la oferta completa en `job_description.md`.
3. Analizar con la skill `job-description-analyzer` y completar `analysis.md`
   (keywords, requisitos, match, brechas, estrategia).
4. Adaptar `applications/<carpeta>/cv.yaml` con `resume-tailor` y
   `resume-bullet-writer`, sin inventar nada.
5. Renderizar con `cv.py render <carpeta>`.
6. Verificar ATS con `resume-ats-optimizer`; ajustar y volver a renderizar.
7. Carta o mensaje con `cover-letter-generator` en `cover_letter.md` (opcional).
8. Registrar envío con `cv.py set-status <carpeta> applied --sent-date YYYY-MM-DD`
   (o la tool MCP `cv_set_status`).

Skills disponibles en `.agents/skills/`. Cada `SKILL.md` describe cuándo usarla.
No cargues todas: elige las que correspondan al paso actual.

## Integración por MCP

El repo incluye `mcp/cv_workspace_server.py`, que expone:
`cv_status`, `cv_list_applications`, `cv_read_cv`, `cv_init`,
`cv_new_application`, `cv_render`, `cv_check`, `cv_set_status`.

- OpenCode: ya configurado en `opencode.json`.
- Claude Code: `.mcp.json` en la raíz.
- Cursor: `.cursor/mcp.json`.
- VS Code/Copilot: `.vscode/mcp.json`.
- Otros clientes: ver `docs/agent-integration.md`.

Prefiere las tools MCP cuando estén disponibles; si no, usa el CLI. No escribas
un servidor MCP alternativo ni dupliques su lógica.

## Skills y compatibilidad

- Fuente única: `.agents/skills/`. OpenCode la lee directamente.
- Claude Code necesita `.claude/skills/`; se genera con `cv.py sync-skills`
  (enlaces simbólicos, con copia como fallback en Windows).
- Si faltan skills: `npx skills experimental_install` y luego `cv.py sync-skills`.
- No borres ni renombres `.agents/skills/*/SKILL.md` a mano; las vendorizadas se
  gestionan con el CLI de skills y `skills-lock.json`. `cv-workspace` es una skill
  local de este repo y no está en el lockfile.

## Validación mínima antes de cerrar una tarea

```bash
python3 scripts/cv.py check
python3 scripts/cv.py sync-skills --check   # si tocaste skills o setup
python3 -m compileall -q scripts mcp        # si tocaste Python
```

Si `check` falla por el PDF y el usuario solo pidió editar contenido, reporta el
error exacto; no lo ocultes ni desactives la validación.

## Estilo de los CVs

- Verbos de acción y resultados medibles cuando existan datos reales.
- Máximo 1 página para prácticas/junior; 2 para senior.
- Sin emojis, sin fotos salvo que la oferta lo pida, sin gráficos de nivel.
- Fechas consistentes (`YYYY-MM` o `YYYY`), sin mezclar formatos.
- Keywords de la oferta integradas en contexto real, nunca en una lista falsa.

## Referencias

- Flujo detallado: `docs/application_workflow.md`
- Agentes y MCP: `docs/agent-integration.md`
- RenderCV 2.8: <https://docs.rendercv.com>
