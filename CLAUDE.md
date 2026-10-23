# CLAUDE.md

Este repositorio usa `AGENTS.md` como fuente única de instrucciones.

@AGENTS.md

Notas específicas de Claude Code:

- Las skills viven en `.agents/skills/`. Ejecuta `python3 scripts/cv.py sync-skills`
  para exponerlas en `.claude/skills/` (enlaces simbólicos; en Windows se copian).
- El servidor MCP del proyecto está declarado en `.mcp.json`; apruébalo la primera
  vez que lo uses.
- No agregues reglas nuevas aquí: actualiza `AGENTS.md` para que todos los agentes
  las vean.
