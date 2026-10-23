# browser-agent-eval (opcional)

Smoke-test para comparar herramientas de navegación orientadas a agentes
(`obscura`, `lightpanda`, `agent-browser`) contra portales de empleo.

**No es parte del flujo principal del CV.** Tiene su propio entorno y sus propias
dependencias pesadas (browser-use, Playwright, LangChain). No lo instales salvo
que quieras experimentar con automatización de portales.

## Uso

```bash
cd tools/browser-agent-eval
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/python portal_smoke_test.py
```

Los resultados quedan en `outputs/` (ignorado por git).

## Qué hace y qué no

- Abre portales de empleo y mide el tamaño del texto que recibe un agente.
- No inicia sesión, no completa formularios y no envía postulaciones.
- No usa datos personales reales.

## Requisitos externos

El script busca binarios en el PATH (`obscura`, `lightpanda`, `agent-browser`) y
falla de forma controlada si no están. Instálalos solo si vas a usar este
experimento.
