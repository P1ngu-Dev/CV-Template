# Instalar y configurar el workspace con un agente

Guía para que un agente de IA (Claude Code, Cursor, Copilot, Gemini CLI, Codex,
OpenCode, Windsurf, Cline…) deje este repositorio listo sin que el usuario tenga
que leer el README.

El agente solo necesita ejecutar un comando idempotente y leer su JSON:

```bash
python3 scripts/cv.py bootstrap --json
```

## Prompt para el usuario

Copia esto en tu agente, dentro del repo ya clonado:

```text
Configura este workspace de CV siguiendo AGENTS.md y docs/agent-setup.md.

1. Ejecuta `python3 scripts/cv.py bootstrap --json` (en Windows usa `python`).
2. Si `next_actions` pide un nombre, pregúntamelo y repite con
   `python3 scripts/cv.py bootstrap --name "Mi Nombre" --json`.
3. Si `ok` es false, muéstrame el `detail` exacto y lo que debo instalar; no
   inventes soluciones ni instales RenderCV globalmente.
4. Cuando `ok` sea true: dime cómo conectar el servidor MCP de mi cliente,
   muéstrame la ruta de main/cv.yaml y el comando para crear mi primera
   postulación.

No modifiques main/cv.yaml más allá de crearlo desde el ejemplo y no hagas commit.
```

Si todavía no tiene el repo:

```text
Clona con git el repositorio <URL> en una carpeta nueva, entra en ella y
configúralo siguiendo AGENTS.md y docs/agent-setup.md. Pregúntame el nombre que
debe llevar el CV antes de crearlo. Al terminar, resume qué instalaste, qué
quedó pendiente y cómo abrir el proyecto en mi cliente de IA.
```

## Qué hace `bootstrap`

Es idempotente: se puede ejecutar las veces que haga falta.

| Paso | Qué comprueba o hace | `required` |
| --- | --- | --- |
| `python` | Python ≥ 3.12 | sí |
| `rendercv` | RenderCV disponible (`.venv`, `PATH` o `RENDERCV`); si falta, crea `.venv` e instala `rendercv[full]==2.8` | sí |
| `skills` | Enlaza `.agents/skills` en `.claude/skills` | sí |
| `master` | Crea `main/cv.yaml` desde el ejemplo solo si pasas `--name` | no |
| `doctor` | Diagnóstico completo del entorno | — |
| `check` | Renderiza todos los `cv.yaml` en un directorio temporal | — |

Opciones:

```bash
python3 scripts/cv.py bootstrap --name "Ana Pérez"   # crea main/cv.yaml
python3 scripts/cv.py bootstrap --no-install         # no instala nada
python3 scripts/cv.py bootstrap --no-check           # omite la validación
python3 scripts/cv.py bootstrap --pdf                # valida compilando PDF
python3 scripts/cv.py bootstrap --json               # contrato para agentes
```

`bootstrap` nunca sobrescribe un `main/cv.yaml` existente. Para reemplazarlo a
propósito: `python3 scripts/cv.py init --force --name "..."`.

## Contrato JSON

```json
{
  "ok": true,
  "steps": [
    {"step": "python", "ok": true, "detail": "Python 3.12.3", "required": true},
    {"step": "rendercv", "ok": true, "detail": "RenderCV v2.8", "required": true},
    {"step": "skills", "ok": true, "detail": "22 skills, 0 enlaces pendientes", "required": true},
    {"step": "master", "ok": false, "detail": "falta main/cv.yaml (pasa --name para crearlo)", "required": false}
  ],
  "doctor": [{"name": "RenderCV disponible", "ok": true, "detail": "...", "required": true}],
  "check": [{"target": "main/example_cv.yaml", "ok": true, "detail": ""}],
  "next_actions": ["python3 scripts/cv.py init --name \"Nombre Apellido\""]
}
```

Cómo interpretarlo:

- `ok` es la única señal de éxito. Exit code `0` si `ok` es true, `1` si no.
- `steps[].required: false` con `ok: false` es un estado válido (por ejemplo, un
  clon nuevo sin CV maestro): falta un paso, pero el entorno está sano.
- `next_actions` son las instrucciones exactas para el usuario; muéstralas tal
  cual, sin reemplazarlas por comandos inventados.
- `check` en `null` significa que la validación se omitió (`--no-check`) o que
  RenderCV no estaba disponible.

## Verificación final

```bash
python3 scripts/cv.py bootstrap --json   # "ok": true
python3 scripts/cv.py doctor             # exit 0, sin FALLA
python3 scripts/cv.py check              # todos los cv.yaml en OK
```

La salida humana de `bootstrap` termina en `Entorno listo.` cuando `ok` es true.

## Conectar el servidor MCP

`bootstrap` no conecta el cliente: cada uno tiene su archivo ya preparado en el
repo. El usuario solo debe aprobarlo o recargarlo.

| Cliente | Archivo | Cómo activarlo |
| --- | --- | --- |
| Claude Code | `.mcp.json` | abrir `claude` y aprobar el servidor; `/mcp` para ver tools |
| Cursor | `.cursor/mcp.json` | Settings → MCP → recargar |
| VS Code / Copilot | `.vscode/mcp.json` | Command Palette → `MCP: List Servers` |
| Gemini CLI | `.gemini/settings.json` | `/mcp` → `reload` |
| Codex | `.codex/config.toml` | marcar el proyecto como confiable; `/mcp` |
| OpenCode | `opencode.json` | `/mcps` |

Detalle por cliente, tools y prompts: [`agent-integration.md`](agent-integration.md).

En Windows hay que cambiar `python3` por `python` en los archivos de
configuración MCP antes de conectar.

## Reglas para el agente

1. **No inventes datos personales.** El nombre se pregunta; el resto del CV lo
   completa el usuario. No agregues experiencia, fechas, títulos ni métricas.
2. **No sobrescribas `main/cv.yaml`.** `bootstrap --name` solo crea el archivo si
   no existe. `--force` requiere pedido explícito del usuario.
3. **No instales RenderCV globalmente.** Usa `.venv` o `pipx`; el CLI resuelve el
   ejecutable solo.
4. **No edites `outputs/`.** Es generado por RenderCV.
5. **No hagas commit** de datos personales ni de `outputs/`; revisa `git status`.
6. **Reporta el resultado real**: `ok`, pasos fallidos y `next_actions`. Si algo
   falla, muestra el `detail` exacto en vez de resumirlo.

## Problemas comunes

| Síntoma | Causa / solución |
| --- | --- |
| `No pude crear el entorno virtual` | Falta `python3-venv`: `sudo apt install python3.12-venv` (Debian/Ubuntu) |
| `pip` bloqueado por PEP 668 | Usa el `.venv` del repo; no instales con `pip --user` global |
| Sin red o proxy corporativo | Usa `--no-install` con un RenderCV ya instalado y `RENDERCV=/ruta/rendercv` |
| `command not found: python3` (Windows) | Usa `python scripts/cv.py ...` |
| Skills en 0 | `npx skills experimental_install` y repite el bootstrap |
| `check` falla solo con `--pdf` | Falta Typst o una fuente; muestra el error de RenderCV, no lo ocultes |
| El MCP no conecta | Verifica `python3 mcp/cv_workspace_server.py` y la ruta de `python` en la config |

## Referencias

- Reglas canónicas: [`../AGENTS.md`](../AGENTS.md)
- Flujo de postulación: [`application_workflow.md`](application_workflow.md)
- Integración por cliente: [`agent-integration.md`](agent-integration.md)
