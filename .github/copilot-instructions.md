# Instrucciones para GitHub Copilot

Lee `AGENTS.md` en la raíz del repositorio: es la fuente única de reglas de este
proyecto. Resumen operativo:

- Es un workspace CV-as-code con RenderCV. `main/cv.yaml` es el CV maestro;
  cada postulación vive en `applications/<YYYY-MM-empresa-rol>/cv.yaml`.
- No inventes experiencia, fechas ni métricas. Adapta contenido existente.
- No edites `outputs/` ni `main/cv.yaml` al adaptar una postulación.
- Comandos: `python scripts/cv.py check`, `python scripts/cv.py render <carpeta>`,
  `python scripts/cv.py new "Empresa" "Rol"`.
- El servidor MCP del proyecto está en `mcp/cv_workspace_server.py`
  (config de VS Code en `.vscode/mcp.json`).
- Documentación: `docs/application_workflow.md` y `docs/agent-integration.md`.

Mantén las respuestas y la documentación en español.
