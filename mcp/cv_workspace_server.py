#!/usr/bin/env python3
"""Servidor MCP del workspace CV (transporte stdio, sin dependencias).

Expone las mismas operaciones que `scripts/cv.py` para que cualquier agente
compatible con Model Context Protocol pueda crear, renderizar y validar CVs sin
adivinar comandos.

Uso manual:
    python3 mcp/cv_workspace_server.py
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cvlib as cv  # noqa: E402, I001

SERVER_NAME = "cv-workspace"
SERVER_VERSION = "0.1.0"
SUPPORTED_PROTOCOLS = ("2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25")
LATEST_PROTOCOL = "2025-06-18"

INSTRUCTIONS = """\
Workspace CV-as-code basado en RenderCV. main/cv.yaml es la fuente de verdad y cada
postulación vive en applications/<YYYY-MM-empresa-rol>/ con su propia copia de cv.yaml.

Reglas:
1. Nunca inventes experiencia, fechas, títulos ni métricas: solo reformula o reordena
   contenido que ya existe en el CV del usuario o que el usuario entregue explícitamente.
2. Al adaptar una postulación, edita applications/<carpeta>/cv.yaml, nunca main/cv.yaml.
3. Antes de decir que algo quedó listo, ejecuta la herramienta cv_check.
4. Los archivos de outputs/ son generados: no los edites a mano.

Flujo típico: cv_status -> cv_new_application -> editar analysis.md y cv.yaml ->
cv_render -> cv_check -> cv_set_status.

Si cv_status indica que falta RenderCV o el CV maestro, pide al usuario ejecutar
`python3 scripts/cv.py bootstrap` (o `--name "Nombre"` para crear main/cv.yaml).
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "cv_status",
        "description": (
            "Resumen del workspace: si existe el CV maestro, versión de RenderCV, "
            "número de postulaciones y skills instaladas."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "cv_list_applications",
        "description": "Lista las postulaciones con empresa, rol, estado y outputs generados.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "cv_read_cv",
        "description": (
            "Devuelve el YAML de un CV. Usa 'main' para el CV maestro o el nombre de la "
            "carpeta dentro de applications/."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "'main' o carpeta de applications/ (ej. 2026-01-acme-intern)",
                    "default": "main",
                }
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "cv_init",
        "description": "Crea main/cv.yaml a partir de main/example_cv.yaml si aún no existe.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre a colocar en el CV"},
                "force": {
                    "type": "boolean",
                    "description": "Sobrescribe main/cv.yaml si ya existe",
                    "default": False,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "cv_new_application",
        "description": (
            "Crea la carpeta de una postulación con README, job_description, analysis, "
            "cover_letter, application_log y una copia del CV maestro."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Nombre de la empresa"},
                "role": {"type": "string", "description": "Nombre del cargo"},
                "url": {"type": "string", "description": "Link de la oferta"},
                "job_text": {
                    "type": "string",
                    "description": "Texto de la oferta para job_description.md",
                },
                "date": {
                    "type": "string",
                    "description": "Fecha base YYYY-MM-DD (default: hoy)",
                },
                "force": {"type": "boolean", "default": False},
            },
            "required": ["company", "role"],
            "additionalProperties": False,
        },
        "annotations": {"destructiveHint": False},
    },
    {
        "name": "cv_render",
        "description": (
            "Renderiza un CV a PDF/Markdown/HTML con RenderCV y devuelve los archivos "
            "generados en su carpeta outputs/."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "'main' o carpeta de applications/",
                    "default": "main",
                },
                "pdf": {
                    "type": "boolean",
                    "description": "Generar PDF (default true). false genera solo Markdown/HTML.",
                    "default": True,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "cv_check",
        "description": (
            "Valida el CV maestro, el ejemplo y todas las postulaciones con RenderCV. "
            "Puede tardar; con pdf=false valida la estructura sin compilar PDF."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pdf": {
                    "type": "boolean",
                    "description": "Incluir compilación de PDF al validar",
                    "default": False,
                }
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "cv_set_status",
        "description": "Actualiza el estado de una postulación en application_log.md y README.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "application": {
                    "type": "string",
                    "description": "Carpeta de la postulación dentro de applications/",
                },
                "status": {
                    "type": "string",
                    "description": "Nuevo estado (draft, applied, interview, offer, rejected...)",
                },
                "sent_date": {
                    "type": "string",
                    "description": "Fecha de envío YYYY-MM-DD (opcional)",
                },
            },
            "required": ["application", "status"],
            "additionalProperties": False,
        },
    },
]


# --------------------------------------------------------------------------
# Implementación de herramientas
# --------------------------------------------------------------------------


def tool_cv_status(_: dict[str, Any]) -> dict[str, Any]:
    return cv.status()


def tool_cv_list_applications(_: dict[str, Any]) -> dict[str, Any]:
    applications = cv.list_applications()
    return {"count": len(applications), "applications": applications}


def tool_cv_read_cv(arguments: dict[str, Any]) -> dict[str, Any]:
    path = cv.resolve_cv(str(arguments.get("target") or "main"))
    return {"path": cv.relative(path), "content": path.read_text(encoding="utf-8")}


def tool_cv_init(arguments: dict[str, Any]) -> dict[str, Any]:
    path = cv.init_master(
        name=arguments.get("name"),
        force=bool(arguments.get("force", False)),
    )
    return {"path": cv.relative(path), "next": "Editar el YAML y ejecutar cv_check."}


def tool_cv_new_application(arguments: dict[str, Any]) -> dict[str, Any]:
    folder = cv.create_application(
        str(arguments["company"]),
        str(arguments["role"]),
        url=str(arguments.get("url") or ""),
        job_text=str(arguments.get("job_text") or ""),
        date=arguments.get("date") or None,
        force=bool(arguments.get("force", False)),
    )
    return {
        "folder": cv.relative(folder),
        "files": sorted(p.name for p in folder.iterdir() if p.is_file()),
        "next": "Completar analysis.md, adaptar cv.yaml y ejecutar cv_render.",
    }


def tool_cv_render(arguments: dict[str, Any]) -> dict[str, Any]:
    cv_file = cv.resolve_cv(str(arguments.get("target") or "main"))
    out_dir = cv.output_dir_for(cv_file)
    payload = cv.render_cv(cv_file, out_dir, pdf=bool(arguments.get("pdf", True)))

    if not payload["ok"]:
        raise RuntimeError(str(payload["stderr"] or payload["stdout"]).strip())

    return {
        "ok": True,
        "cv": cv.relative(cv_file),
        "output": cv.relative(out_dir),
        "generated": sorted(p.name for p in out_dir.iterdir() if p.is_file()),
    }


def tool_cv_check(arguments: dict[str, Any]) -> dict[str, Any]:
    results = cv.check_all(pdf=bool(arguments.get("pdf", False)))
    return {
        "ok": all(result.ok for result in results),
        "results": [result.as_dict() for result in results],
    }


def tool_cv_set_status(arguments: dict[str, Any]) -> dict[str, Any]:
    folder = cv.set_application_status(
        str(arguments["application"]),
        str(arguments["status"]),
        sent_date=arguments.get("sent_date"),
    )
    return {"folder": cv.relative(folder), "status": arguments["status"]}


HANDLERS = {
    "cv_status": tool_cv_status,
    "cv_list_applications": tool_cv_list_applications,
    "cv_read_cv": tool_cv_read_cv,
    "cv_init": tool_cv_init,
    "cv_new_application": tool_cv_new_application,
    "cv_render": tool_cv_render,
    "cv_check": tool_cv_check,
    "cv_set_status": tool_cv_set_status,
}


# --------------------------------------------------------------------------
# JSON-RPC sobre stdio
# --------------------------------------------------------------------------


def _text_result(text: str, *, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _pretty(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, ensure_ascii=False, indent=2)


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    # Notificaciones: no llevan respuesta.
    if request_id is None and method and method.startswith("notifications/"):
        return None

    def ok(result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def error(code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    if method == "initialize":
        requested = params.get("protocolVersion")
        protocol = requested if requested in SUPPORTED_PROTOCOLS else LATEST_PROTOCOL
        return ok(
            {
                "protocolVersion": protocol,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": INSTRUCTIONS,
            }
        )

    if method == "ping":
        return ok({})

    if method == "tools/list":
        return ok({"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}

        handler = HANDLERS.get(name)
        if handler is None:
            return error(-32602, f"Herramienta desconocida: {name}")

        try:
            payload = handler(arguments)
        except cv.CvError as exc:
            return ok(_text_result(f"ERROR: {exc}", is_error=True))
        except Exception as exc:  # noqa: BLE001 - el servidor no debe morir por una tool
            traceback.print_exc(file=sys.stderr)
            return ok(_text_result(f"ERROR inesperado: {exc}", is_error=True))

        return ok(_text_result(_pretty(payload)))

    return error(-32601, f"Método no soportado: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            print(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": f"JSON inválido: {exc}"},
                    }
                ),
                flush=True,
            )
            continue

        if not isinstance(request, dict):
            continue

        response = handle_request(request)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None
