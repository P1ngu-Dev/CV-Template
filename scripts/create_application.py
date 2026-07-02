#!/usr/bin/env python3
"""Create a per-application CV workspace from the master CV and templates.

Usage examples:
  scripts/create_application.py "Banco BICE" "Práctica Ing Informática Programación" --url https://www.linkedin.com/jobs/view/4431757396/
  scripts/create_application.py "Vambe" "Software Engineer Intern" --job-file /tmp/vambe.md
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLICATIONS = ROOT / "applications"
TEMPLATES = ROOT / "templates"
MASTER_CV = ROOT / "main" / "cv.yaml"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return re.sub(r"-+", "-", value)[:80] or "postulacion"


def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_new(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Ya existe: {path}. Usa --force para sobrescribir archivos generados.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea carpeta de postulación desde templates y copia main/cv.yaml.")
    parser.add_argument("company", help="Empresa, ej. Banco BICE")
    parser.add_argument("role", help="Rol, ej. Práctica Ing Informática Programación")
    parser.add_argument("--url", default="", help="Link de la oferta")
    parser.add_argument("--job-file", type=Path, help="Archivo markdown/txt con la descripción de la oferta")
    parser.add_argument("--date", default=date.today().isoformat(), help="Fecha base YYYY-MM-DD; default hoy")
    parser.add_argument("--force", action="store_true", help="Sobrescribe archivos generados si ya existen")
    args = parser.parse_args()

    if not MASTER_CV.exists():
        print(f"No existe CV maestro: {MASTER_CV}", file=sys.stderr)
        return 2

    ym = args.date[:7]
    folder = APPLICATIONS / f"{ym}-{slugify(args.company)}-{slugify(args.role)}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "outputs").mkdir(exist_ok=True)

    job_text = ""
    if args.job_file:
        if not args.job_file.exists():
            print(f"No existe --job-file: {args.job_file}", file=sys.stderr)
            return 2
        job_text = args.job_file.read_text(encoding="utf-8")

    shutil.copyfile(MASTER_CV, folder / "cv.yaml")

    readme = f"""# {args.company} — {args.role}

## Estado

draft

## Archivos

- `job_description.md`: oferta original o resumen fiel.
- `analysis.md`: análisis de match, keywords y cambios sugeridos.
- `cv.yaml`: copia derivada de `../../main/cv.yaml`; editar solo esta versión.
- `outputs/`: salidas generadas por RenderCV.
- `cover_letter.md`: carta/mensaje si la postulación lo requiere.
- `application_log.md`: seguimiento de envío.

## Flujo rápido

1. Completar `job_description.md` si falta texto de la oferta.
2. Completar `analysis.md` con requisitos, keywords y estrategia.
3. Adaptar `cv.yaml` sin inventar experiencia.
4. Ejecutar desde la raíz del repo:
   `scripts/render_application.sh {folder.relative_to(ROOT)}`
5. Revisar `outputs/` y registrar envío en `application_log.md`.
"""

    jd = f"""# Job Description — {args.company} — {args.role}

- Empresa: {args.company}
- Rol: {args.role}
- Link: {args.url or 'Pendiente'}
- Fecha de captura: {args.date}

## Oferta

{job_text.strip() if job_text.strip() else 'Pegar aquí la oferta original o un resumen fiel.'}
"""

    analysis = f"""# Análisis de Oferta — {args.company} — {args.role}

## Veredicto rápido

Pendiente.

## Keywords clave

- Pendiente.

## Requisitos obligatorios

- Pendiente.

## Requisitos deseables

- Pendiente.

## Match con CV actual

- Pendiente.

## Cambios sugeridos para el CV

- Pendiente.

## Riesgos / brechas

- Pendiente.

## Estrategia de postulación

- Pendiente.
"""

    cover = f"""# Carta / Mensaje de Presentación — {args.company} — {args.role}

Pendiente. Generar solo si la postulación lo pide o si conviene enviar un mensaje breve al reclutador.
"""

    log = f"""# Application Log — {args.company} — {args.role}

## Empresa

{args.company}

## Rol

{args.role}

## Fecha de creación

{args.date}

## Fecha de envío

Pendiente

## Link de la oferta

{args.url or 'Pendiente'}

## Contacto

Pendiente

## Estado

draft

## Notas de seguimiento

- Carpeta creada con `scripts/create_application.py`.
"""

    write_new(folder / "README.md", readme, args.force)
    write_new(folder / "job_description.md", jd, args.force)
    write_new(folder / "analysis.md", analysis, args.force)
    write_new(folder / "cover_letter.md", cover, args.force)
    write_new(folder / "application_log.md", log, args.force)

    print(folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
