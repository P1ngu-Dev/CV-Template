# Contribuir

Este repo es una plantilla de CV-as-code. Las contribuciones deben mantener la
portabilidad: cualquiera debe poder clonar, ejecutar dos comandos y renderizar.

## Antes de abrir un PR

```bash
# Dependencias de desarrollo (ruff)
.venv/bin/pip install -e ".[dev]"

python3 scripts/cv.py doctor
python3 scripts/cv.py check
python3 scripts/cv.py sync-skills --check
python3 -m compileall -q scripts mcp
ruff check scripts mcp
```

Si tocaste Python, agrega o ajusta la verificación correspondiente en
`.github/workflows/ci.yml`.

## Reglas

- **Sin datos personales.** No agregues CVs reales, correos, teléfonos ni
  direcciones. Usa `example` o datos ficticios.
- **Una sola fuente de lógica.** Si cambias el comportamiento del CLI, hazlo en
  `scripts/cvlib.py`; el servidor MCP lo reutiliza.
- **Plantillas con placeholders.** Usa `{{COMPANY}}`, `{{ROLE}}`, `{{DATE}}`,
  `{{URL_OR_PENDING}}`, `{{JOB_TEXT}}` y `{{FOLDER_NAME}}`. No hardcodees
  contenido de postulaciones en Python.
- **Idioma:** documentación en español; nombres de código en inglés.
- **Sin dependencias nuevas** para el flujo principal. `rendercv[full]` es la
  única dependencia de runtime; el resto debe ser stdlib.

## Estructura de un cambio

1. Describe el problema y el cambio esperado.
2. Si afecta el flujo, actualiza `AGENTS.md` y `docs/`.
3. Verifica localmente los cuatro comandos de arriba.
4. Abre el PR con el resultado de `cv.py check` pegado.
