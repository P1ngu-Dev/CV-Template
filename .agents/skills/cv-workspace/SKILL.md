---
name: cv-workspace
description: Flujo completo del workspace CV-as-code: crear postulación, adaptar el CV con RenderCV, renderizar y validar. Úsala cuando trabajes en main/cv.yaml o en applications/.
---

# CV Workspace

Skill local de este repositorio (no viene del lockfile de skills). Resume el flujo
que debes seguir y las reglas que no puedes romper.

## Cuándo usarla

- Crear una postulación nueva.
- Adaptar `applications/<carpeta>/cv.yaml` a una oferta.
- Renderizar o validar un CV.
- Revisar el estado del workspace.

## Comandos

```bash
python3 scripts/cv.py status
python3 scripts/cv.py new "Empresa" "Rol" --url "https://..."
python3 scripts/cv.py render <carpeta|main>
python3 scripts/cv.py check
python3 scripts/cv.py set-status <carpeta> applied --sent-date YYYY-MM-DD
```

## Reglas

1. `main/cv.yaml` es el maestro; no lo edites para una postulación puntual.
2. No inventes experiencia, fechas, títulos ni métricas.
3. `outputs/` es generado; no lo edites.
4. Valida con `check` antes de declarar que terminaste.
5. Una postulación por carpeta; no reutilices carpetas.

## Archivos clave

- `AGENTS.md`: reglas completas y mapa del repo.
- `docs/application_workflow.md`: flujo paso a paso.
- `templates/`: placeholders usados por `cv.py new`.
- `mcp/cv_workspace_server.py`: las mismas operaciones por MCP.

## Skills relacionadas

`job-description-analyzer` para analizar la oferta, `resume-tailor` y
`resume-bullet-writer` para adaptar, `resume-ats-optimizer` para verificar ATS,
`cover-letter-generator` para la carta.
