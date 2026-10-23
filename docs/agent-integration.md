# Integración con agentes de IA

Este repo está preparado para que un agente (Claude Code, Cursor, Copilot, Gemini
CLI, Codex, OpenCode, Windsurf, Cline...) lo entienda sin explicarle nada y pueda
ejecutar el flujo completo.

## Las tres piezas

| Pieza | Archivo | Para qué |
| --- | --- | --- |
| Instrucciones | `AGENTS.md` | Reglas, comandos, mapa del repo y flujo |
| Skills | `.agents/skills/` | 22 skills de CV, ATS, cartas y entrevistas |
| Herramientas | `mcp/cv_workspace_server.py` | Crear, renderizar y validar por MCP |

`AGENTS.md` es la fuente única. Los demás archivos solo apuntan a él o agregan
detalles del cliente.

## Compatibilidad por cliente

| Cliente | Instrucciones | MCP | Skills |
| --- | --- | --- | --- |
| **OpenCode** | `AGENTS.md` (automático) | `opencode.json` | `.agents/skills` (automático) |
| **Claude Code** | `CLAUDE.md` → `AGENTS.md` | `.mcp.json` | `.claude/skills` (generado con `sync-skills`) |
| **Cursor** | `.cursor/rules/cv-workspace.mdc` + `AGENTS.md` | `.cursor/mcp.json` | vía `AGENTS.md` o el directorio de skills de tu versión |
| **GitHub Copilot / VS Code** | `.github/copilot-instructions.md` | `.vscode/mcp.json` | vía `AGENTS.md` (no hay directorio de skills nativo) |
| **Gemini CLI** | `GEMINI.md` → `AGENTS.md` | `.gemini/settings.json` | vía `AGENTS.md` |
| **Codex CLI** | `AGENTS.md` (automático) | `.codex/config.toml` (proyecto confiable) | vía `AGENTS.md` |
| **Windsurf / Cline / otros** | `AGENTS.md` | configurar manualmente | vía `AGENTS.md` |

En Windows, reemplaza `python3` por `python` en todos los archivos de
configuración MCP.

## Servidor MCP

Es un proceso local, por stdio, **sin dependencias externas**. No hace peticiones
de red: solo lee y escribe dentro del repo.

Arranque manual para probarlo:

```bash
python3 mcp/cv_workspace_server.py
```

Puedes enviarle un JSON-RPC por línea:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"manual","version":"0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"cv_status","arguments":{}}}
```

### Tools disponibles

| Tool | Argumentos | Qué hace |
| --- | --- | --- |
| `cv_status` | — | Estado del workspace y de RenderCV |
| `cv_list_applications` | — | Postulaciones con empresa, rol y estado |
| `cv_read_cv` | `target` | Devuelve el YAML del maestro o de una postulación |
| `cv_init` | `name`, `force` | Crea `main/cv.yaml` desde el ejemplo |
| `cv_new_application` | `company`, `role`, `url`, `job_text`, `date`, `force` | Crea la carpeta completa |
| `cv_render` | `target`, `pdf` | Renderiza a `outputs/` |
| `cv_check` | `pdf` | Valida maestro, ejemplo y postulaciones |
| `cv_set_status` | `application`, `status`, `sent_date` | Actualiza el seguimiento |

Todas las tools devuelven texto (normalmente JSON) y marcan `isError` cuando algo
falla. `outputs/` nunca se edita desde el servidor: se regenera.

### Verificar la conexión

- **OpenCode**: `/mcps` debe mostrar `cv-workspace` conectado.
- **Claude Code**: `claude mcp list` o `/mcp`.
- **Cursor**: Settings → MCP; el servidor aparece como `cv-workspace`.
- **VS Code**: Command Palette → `MCP: List Servers`.
- **Gemini CLI**: `/mcp` y elige `reload`.
- **Codex**: `/mcp` dentro de la TUI o `codex mcp list`.

## Prompts de ejemplo

Crear una postulación completa:

```text
Lee AGENTS.md. Crea una postulación para "Acme" como "Backend Intern" con esta
oferta: <pega la oferta>. Completa analysis.md, adapta cv.yaml sin inventar nada,
renderiza y valida con cv_check. Al final muéstrame el match, las brechas y la
ruta del PDF.
```

Adaptar sin tocar el maestro:

```text
Adapta solo applications/2026-02-acme-backend-intern/cv.yaml para priorizar
Python, SQL y Docker. No modifiques main/cv.yaml ni inventes métricas. Después
ejecuta cv_render y cv_check.
```

Revisión ATS:

```text
Usa la skill resume-ats-optimizer sobre el cv.yaml de la postulación activa.
Dame una lista de cambios concretos, aplícalos y vuelve a renderizar.
```

Seguimiento:

```text
Revisa cv_list_applications y dime qué postulaciones llevan más de 10 días sin
respuesta. Actualiza el estado de las que ya envié según estas notas: ...
```

## Skills

Fuente única: `.agents/skills/`. OpenCode las descubre automáticamente y
Claude Code las consume desde `.claude/skills`.

En los demás clientes, las skills quedan disponibles como documentación
estructurada: el agente puede leer `.agents/skills/<nombre>/SKILL.md` cuando
`AGENTS.md` o el usuario se lo indiquen. No las copies a mano a otros
directorios: si tu cliente soporta un directorio de skills, apunta su
configuración a `.agents/skills`.

Claude Code solo mira `.claude/skills`, así que se generan enlaces:

```bash
python3 scripts/cv.py sync-skills
python3 scripts/cv.py sync-skills --check   # para CI
```

En Windows sin permisos de symlink, el script copia las skills automáticamente.
Si el repo se clona sin las skills:

```bash
npx skills experimental_install
python3 scripts/cv.py sync-skills
```

`skills-lock.json` (raíz) es el lockfile canónico. No agregues un segundo
lockfile dentro de `.agents/skills/`.

## Privacidad y límites

- El servidor MCP solo opera dentro del repositorio; no sube archivos a ningún
  servicio.
- Aun así, el agente que lo usa puede tener acceso a la conversación: no pegues
  datos sensibles que no quieras que el proveedor del modelo vea.
- `outputs/` está en `.gitignore` porque los PDFs contienen datos personales.
- En un fork público, revisa `git status` antes de cada commit.

## Problemas comunes

| Síntoma | Causa / solución |
| --- | --- |
| El MCP no conecta | Verifica `python3 mcp/cv_workspace_server.py` a mano y que el JSON-RPC responda |
| `command not found: python3` en Windows | Cambia `python3` por `python` en la config del cliente |
| El servidor conecta pero `cv_render` falla | Falta RenderCV: `python3 scripts/cv.py setup` |
| El agente no sigue las reglas | Asegúrate de que lea `AGENTS.md`; en Claude/Cursor el puente debe existir |
| Un cliente no ve las skills | Ejecuta `sync-skills`; para clientes no listados, apunta su config a `.agents/skills` |
| Codex ignora `.codex/config.toml` | El proyecto debe estar marcado como confiable |

Diagnóstico general: `python3 scripts/cv.py doctor`.
