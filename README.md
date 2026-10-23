# CV Workspace

Plantilla de **CV-as-code**: escribes tu CV una vez en YAML, RenderCV lo
convierte en PDF/Markdown/HTML, y cada postulación tiene su propia carpeta con
versión adaptada, análisis de la oferta y seguimiento.

Diseñada para dos usos:

1. **Plantilla pública**: otras personas la clonan y la usan con sus propios datos.
2. **Workspace personal**: versionas tu CV real en un fork privado.

Incluye integración lista para agentes de IA (Claude Code, Cursor, Copilot,
Gemini, Codex, OpenCode) mediante `AGENTS.md` y un servidor MCP local.

## Requisitos

- **Python 3.12+** (lo exige RenderCV 2.8).
- Git.
- Opcional: `make` y `npx` (para restaurar skills).

No necesitas instalar RenderCV globalmente: el CLI crea un `.venv` propio.

## Inicio rápido

```bash
git clone https://github.com/P1ngu-Dev/CV-Template.git mi-cv
cd mi-cv

python3 scripts/cv.py setup                       # .venv + RenderCV + skills
python3 scripts/cv.py init --name "Tu Nombre"     # crea main/cv.yaml
python3 scripts/cv.py check                       # valida que todo renderice
```

En Windows usa `python` en lugar de `python3`. Si usas `uv` o `pipx` y prefieres
no crear `.venv`:

```bash
pipx install "rendercv[full]==2.8"
```

El CLI detecta RenderCV en `.venv`, en el `PATH` o en la variable `RENDERCV`.

### Usar esta plantilla

- **Para tu propio CV:** en GitHub usa **Use this template** (o clona) y crea un
  repositorio **privado**; tus datos personales no deben quedar públicos.
- **Para contribuir a la plantilla:** clona este repo y sigue
  [`CONTRIBUTING.md`](CONTRIBUTING.md). No agregues CVs reales.
- **Para probar sin datos reales:** `applications/example/` ya trae una
  postulación completa de demostración.

## Estructura

```text
main/
  cv.yaml              Tu CV maestro (fuente de verdad)
  example_cv.yaml      Ejemplo completo y válido
applications/
  example/             Postulación de demostración de punta a punta
  YYYY-MM-empresa-rol/ Una carpeta por postulación real
templates/             Plantillas con placeholders
scripts/cv.py          CLI única
scripts/cvlib.py       Lógica compartida con el servidor MCP
mcp/                   Servidor MCP (stdio, sin dependencias)
docs/                  Flujo de postulación e integración con agentes
.agents/skills/        Skills de CV (fuente única)
contexts/              Contexto personal/profesional fechado (YYYY-MM-DD.md)
portfolio/             Casos de estudio para portafolio
linkedin/              Versiones del perfil de LinkedIn
references/            Referencias profesionales y académicas
certifications/        Certificados y credenciales
deliveries/            Entregables finales para el usuario o cliente
extern-people/         Contactos y datos de personas externas
archive/               Material histórico, no es fuente de verdad
tmp/                   Archivo temporal local (no versionado)
tools/                 Utilidades opcionales y aisladas
```

## Flujo de una postulación

```bash
# 1. Crear la carpeta
python3 scripts/cv.py new "Banco BICE" "Práctica Informática" \
  --url "https://www.linkedin.com/jobs/view/..." \
  --job-file ~/Descargas/oferta.md

# 2. Completar analysis.md y adaptar cv.yaml

# 3. Renderizar
python3 scripts/cv.py render 2026-02-banco-bice-practica-informatica

# 4. Validar y registrar el envío
python3 scripts/cv.py check
python3 scripts/cv.py set-status 2026-02-banco-bice-practica-informatica applied \
  --sent-date 2026-02-03
```

Resultado: `applications/<carpeta>/outputs/` con PDF, HTML, Markdown y Typst.
El detalle completo está en [`docs/application_workflow.md`](docs/application_workflow.md).

## Comandos

| Comando | Qué hace |
| --- | --- |
| `cv.py setup` | Crea `.venv`, instala RenderCV y enlaza skills |
| `cv.py init --name "..."` | Crea `main/cv.yaml` desde el ejemplo |
| `cv.py new "Empresa" "Rol"` | Crea carpeta de postulación + archivos |
| `cv.py render [main\|carpeta]` | Renderiza a `outputs/` |
| `cv.py check [--pdf]` | Valida maestro, ejemplo y postulaciones |
| `cv.py list` | Tabla de postulaciones y estados |
| `cv.py status` | Resumen del entorno |
| `cv.py doctor` | Diagnóstico de dependencias y enlaces |
| `cv.py set-status <carpeta> <estado>` | Actualiza seguimiento |
| `cv.py sync-skills` | Enlaza `.agents/skills` a `.claude/skills` |

Con `make`: `make setup`, `make init NAME="..."`, `make new COMPANY="..." ROLE="..."`,
`make render APP=...`, `make check`, `make list`, `make doctor`.

## Agentes de IA

El repo trae instrucciones y herramientas para que un agente trabaje sin
adivinar comandos:

- **`AGENTS.md`**: reglas canónicas (no inventar experiencia, no tocar el maestro
  al adaptar, validar antes de cerrar).
- **Puentes de compatibilidad**: `CLAUDE.md`, `GEMINI.md`,
  `.github/copilot-instructions.md`, `.cursor/rules/cv-workspace.mdc`.
- **Servidor MCP** en `mcp/cv_workspace_server.py` con tools `cv_status`,
  `cv_new_application`, `cv_read_cv`, `cv_render`, `cv_check`,
  `cv_set_status`, entre otras. Ya declarado en `.mcp.json` (Claude Code),
  `.cursor/mcp.json`, `.vscode/mcp.json` y `opencode.json`.
- **Skills**: 22 skills de CV/ATS/entrevistas en `.agents/skills/`.

Guía por cliente y ejemplos de prompts: [`docs/agent-integration.md`](docs/agent-integration.md).

## Privacidad

Este repo es una **plantilla pública**. Antes de publicar tu fork:

- Revisa que `main/cv.yaml` no tenga tu teléfono, correo personal o dirección.
- `applications/` puede contener datos de empresas y reclutadores.
- `outputs/` está en `.gitignore` porque los PDFs incluyen datos personales.

Recomendación: mantén este repo como plantilla y tu CV real en un fork privado.
Puedes usar `main/example_cv.yaml` como base para no partir de cero.

## Skills

Las skills se instalan y versionan con el CLI de skills:

```bash
npx skills experimental_install   # restaura desde skills-lock.json
python3 scripts/cv.py sync-skills # enlaza a .claude/skills
```

`.agents/skills/` es la fuente única. No edites las skills vendorizadas.

## Problemas comunes

| Síntoma | Solución |
| --- | --- |
| `RenderCV no está instalado` | `python3 scripts/cv.py setup` |
| `No existe main/cv.yaml` | `python3 scripts/cv.py init --name "Tu Nombre"` |
| Error de `venv` en Debian/Ubuntu | `sudo apt install python3-venv` o usa `pipx` |
| El PDF no compila | `python3 scripts/cv.py check --pdf` y revisa el error de Typst |
| Un agente no ve las skills | `python3 scripts/cv.py sync-skills` |
| El MCP no conecta en Windows | Cambia `python3` por `python` en la config del cliente |

Diagnóstico general: `python3 scripts/cv.py doctor`.

## Créditos

- RenderCV: <https://github.com/rendercv/rendercv>
- Skills de CV: [Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills)
- Licencia: MIT (ver [`LICENSE`](LICENSE)).
