#!/usr/bin/env python3
"""CLI único del workspace CV.

Ejemplos:
  python3 scripts/cv.py bootstrap --name "Jane Doe"
  python3 scripts/cv.py setup
  python3 scripts/cv.py init --name "Jane Doe"
  python3 scripts/cv.py new "Banco BICE" "Práctica Informática" --url https://...
  python3 scripts/cv.py render 2026-01-banco-bice-practica-informatica
  python3 scripts/cv.py check
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cvlib as cv  # noqa: E402, I001


# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------


def _install_environment() -> None:
    """Crea `.venv` e instala RenderCV. Idempotente: reutiliza el entorno existente."""
    if sys.version_info < cv.MIN_PYTHON:
        raise cv.CvError(
            f"Se requiere Python {cv.MIN_PYTHON[0]}.{cv.MIN_PYTHON[1]}+ "
            f"y estás usando {sys.version.split()[0]}."
        )

    venv_dir = cv.ROOT / ".venv"
    if not venv_dir.exists():
        print("Creando .venv ...")
        proc = cv.run([sys.executable, "-m", "venv", str(venv_dir)], timeout=300)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip()
            raise cv.CvError(
                "No pude crear el entorno virtual.\n"
                f"{detail}\n\n"
                "En Debian/Ubuntu instala el soporte de venv:\n"
                f"  sudo apt install python{sys.version_info.major}.{sys.version_info.minor}-venv\n"
                "O usa directamente: pipx install 'rendercv[full]==2.8'"
            )

    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        raise cv.CvError(f"El entorno {venv_dir} parece incompleto. Bórralo y reintenta.")

    for command, timeout in (
        ([str(python), "-m", "pip", "install", "--upgrade", "pip"], 600),
        ([str(python), "-m", "pip", "install", "-e", "."], 1800),
    ):
        proc = cv.run(command, timeout=timeout)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip()
            raise cv.CvError(f"Falló: {' '.join(command)}\n{detail}")

    print(f"OK RenderCV {cv.rendercv_version()} instalado en .venv")


def cmd_setup(args: argparse.Namespace) -> int:
    _install_environment()

    if not args.no_skills:
        try:
            report = cv.sync_skills(force=True)
            for target, info in report["targets"].items():
                print(f"OK skills -> {target} ({info['created']} enlazadas)")
        except cv.CvError as exc:
            print(f"AVISO: no se enlazaron skills: {exc}", file=sys.stderr)

    print("\nSiguiente paso:")
    if not cv.MASTER_CV.exists():
        print('  python3 scripts/cv.py init --name "Tu Nombre"')
    else:
        print("  python3 scripts/cv.py check")
    return 0


def _bootstrap_report(
    args: argparse.Namespace,
    steps: list[dict[str, object]],
    checks: list[dict[str, object]],
    results: list[cv.CheckResult] | None,
    next_actions: list[str],
) -> int:
    required_ok = all(step["ok"] for step in steps if step["required"])
    doctor_ok = all(check["ok"] for check in checks if check["required"])
    check_ok = results is None or all(result.ok for result in results)
    ok = required_ok and doctor_ok and check_ok

    payload = {
        "ok": ok,
        "steps": steps,
        "doctor": checks,
        "check": None if results is None else [result.as_dict() for result in results],
        "next_actions": next_actions,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if ok else 1

    for step in steps:
        mark = "OK   " if step["ok"] else ("FALLA" if step["required"] else "PENDIENTE")
        print(f"{mark} {step['step']}: {step['detail']}")

    if steps and not doctor_ok:
        print("\nDiagnóstico:")
        for check in checks:
            if check["ok"]:
                continue
            mark = "FALLA" if check["required"] else "AVISO"
            print(f"  {mark} {check['name']}: {check['detail']}")

    if results is not None:
        print("\nValidación:")
        for result in results:
            print(f"  {'OK  ' if result.ok else 'FALLA'} {result.target}")

    if next_actions:
        print("\nSiguiente:")
        for action in next_actions:
            print(f"  - {action}")

    print("\nEntorno listo." if ok else "\nQuedan pasos pendientes.")
    return 0 if ok else 1


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """Deja el workspace listo de una sola vez y reporta qué falta.

    Pensado para agentes: es idempotente y con `--json` devuelve un contrato
    estable (`ok`, `steps`, `doctor`, `check`, `next_actions`).
    """
    steps: list[dict[str, object]] = []
    next_actions: list[str] = []

    def add_step(name: str, ok: bool, detail: str, *, required: bool = True) -> None:
        steps.append({"step": name, "ok": bool(ok), "detail": detail, "required": required})

    python_ok = sys.version_info >= cv.MIN_PYTHON
    add_step("python", python_ok, f"Python {sys.version.split()[0]}")
    if not python_ok:
        next_actions.append(
            f"Instala Python {cv.MIN_PYTHON[0]}.{cv.MIN_PYTHON[1]}+ y vuelve a ejecutar "
            "el bootstrap."
        )
        return _bootstrap_report(args, steps, [], None, next_actions)

    try:
        cv.rendercv_command()
        rendercv_available = True
    except cv.CvError:
        rendercv_available = False

    if rendercv_available:
        add_step("rendercv", True, cv.rendercv_version())
    elif args.no_install:
        add_step("rendercv", False, "no instalado (--no-install)")
        next_actions.append("python3 scripts/cv.py setup")
    else:
        try:
            _install_environment()
            add_step("rendercv", True, cv.rendercv_version())
        except (cv.CvError, subprocess.TimeoutExpired) as exc:
            detail = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
            add_step("rendercv", False, detail)
            next_actions.append(
                "Revisa el error de instalación y ejecuta `python3 scripts/cv.py setup`."
            )

    try:
        report = cv.sync_skills()
        missing = sum(len(info["missing"]) for info in report["targets"].values())
        add_step("skills", report["ok"], f"{report['skills']} skills, {missing} enlaces pendientes")
        if not report["ok"]:
            next_actions.append("python3 scripts/cv.py sync-skills --force")
    except cv.CvError as exc:
        add_step("skills", False, str(exc).splitlines()[0])
        next_actions.append("npx skills experimental_install")

    if cv.MASTER_CV.exists():
        add_step("master", True, cv.relative(cv.MASTER_CV), required=False)
    elif args.name:
        try:
            cv.init_master(name=args.name)
            add_step("master", True, f"{cv.relative(cv.MASTER_CV)} creado a partir del ejemplo")
            next_actions.append(
                f"Edita {cv.relative(cv.MASTER_CV)} con los datos reales del usuario."
            )
        except cv.CvError as exc:
            add_step("master", False, str(exc).splitlines()[0])
    else:
        add_step(
            "master",
            False,
            "falta main/cv.yaml (pasa --name para crearlo)",
            required=False,
        )
        next_actions.append('python3 scripts/cv.py init --name "Nombre Apellido"')

    checks = cv.doctor()
    if not checks:
        next_actions.append("python3 scripts/cv.py doctor")

    results: list[cv.CheckResult] | None = None
    rendercv_ok = any(step["step"] == "rendercv" and step["ok"] for step in steps)
    if not args.no_check and rendercv_ok:
        try:
            results = cv.check_all(pdf=args.pdf)
        except cv.CvError as exc:
            add_step("check", False, str(exc).splitlines()[0])
            next_actions.append("Revisa los cv.yaml y ejecuta `python3 scripts/cv.py check`.")

    if not next_actions:
        next_actions.append(
            'Crea una postulación: python3 scripts/cv.py new "Empresa" "Rol" --url "..."'
        )
        next_actions.append("Conecta el servidor MCP del cliente y verifica con `cv_status`.")

    return _bootstrap_report(args, steps, checks, results, next_actions)


def cmd_init(args: argparse.Namespace) -> int:
    path = cv.init_master(name=args.name, force=args.force)
    print(f"OK CV maestro creado: {cv.relative(path)}")
    print("Edítalo con tus datos reales y luego valida:")
    print("  python3 scripts/cv.py check")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    job_text = ""
    if args.job_file:
        job_file = Path(args.job_file)
        if not job_file.exists():
            raise cv.CvError(f"No existe --job-file: {args.job_file}")
        job_text = job_file.read_text(encoding="utf-8")

    folder = cv.create_application(
        args.company,
        args.role,
        url=args.url,
        job_text=job_text,
        date=args.date,
        force=args.force,
    )
    print(f"OK postulación creada: {cv.relative(folder)}")
    print("\nSiguiente paso:")
    print(f"  1. Completar {cv.relative(folder / 'job_description.md')}")
    print(f"  2. Adaptar {cv.relative(folder / 'cv.yaml')}")
    print(f"  3. Renderizar: python3 scripts/cv.py render {folder.name}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    cv_file = cv.resolve_cv(args.target)
    out_dir = cv.output_dir_for(cv_file)

    payload = cv.render_cv(
        cv_file,
        out_dir,
        pdf=not args.no_pdf,
        png=args.png,
    )
    if not payload["ok"]:
        raise cv.CvError(
            "RenderCV falló.\n\n"
            f"{payload['stderr'] or payload['stdout']}".strip()
        )

    generated = sorted(p.name for p in out_dir.iterdir() if p.is_file())
    print(f"OK {cv.relative(cv_file)} -> {cv.relative(out_dir)}")
    for name in generated:
        print(f"  - {name}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    results = cv.check_all(pdf=args.pdf)

    if args.json:
        print(json.dumps([r.as_dict() for r in results], ensure_ascii=False, indent=2))
        return 0 if all(result.ok for result in results) else 1

    for result in results:
        print(f"{'OK  ' if result.ok else 'FALLA'} {result.target}")
        if result.detail:
            for line in result.detail.splitlines():
                print(f"      {line}")

    failures = [r for r in results if not r.ok]
    if failures:
        print(f"\n{len(failures)} archivo(s) con errores.", file=sys.stderr)
        return 1
    print(f"\nOK: {len(results)} archivo(s) validados.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    applications = cv.list_applications()
    if args.json:
        print(json.dumps(applications, ensure_ascii=False, indent=2))
        return 0

    if not applications:
        print("No hay postulaciones todavía.")
        print('Crea una con: python3 scripts/cv.py new "Empresa" "Rol"')
        return 0

    headers = ("CARPETA", "EMPRESA", "ROL", "ESTADO", "ENVIADA")
    rows = [
        (
            str(item["folder"]),
            str(item["company"]),
            str(item["role"]),
            str(item["status"]),
            str(item["sent"]),
        )
        for item in applications
    ]
    widths = [
        min(max(len(row[index]) for row in [headers, *rows]), 40)
        for index in range(len(headers))
    ]

    def line(row: tuple[str, ...]) -> str:
        cells = [
            value if len(value) <= widths[index] else value[: widths[index] - 1] + "…"
            for index, value in enumerate(row)
        ]
        return "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells))

    print(line(headers))
    print(line(tuple("-" * width for width in widths)))
    for row in rows:
        print(line(row))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    data = cv.status()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    rendercv = data["rendercv"]
    print(f"Repo:        {data['root']}")
    print(f"Python:      {data['python']}")
    print(
        "RenderCV:    "
        + (
            f"{rendercv['version']} ({rendercv['command']})"
            if rendercv["found"]
            else "no instalado — ejecuta `python3 scripts/cv.py setup`"
        )
    )
    print(f"CV maestro:  {'sí' if data['master_cv']['exists'] else 'no (falta `cv.py init`)'}")
    print(f"Postulaciones: {data['applications']}")
    print(f"Skills:      {data['skills']['installed']} en .agents/skills")
    print(f"AGENTS.md:   {'sí' if data['agents']['agents_md'] else 'no'}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = cv.doctor()

    if args.json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
        return 0 if not any(c["required"] and not c["ok"] for c in checks) else 1

    for check in checks:
        mark = "OK   " if check["ok"] else ("FALLA" if check["required"] else "AVISO")
        print(f"{mark} {check['name']}: {check['detail']}")

    failures = [c for c in checks if c["required"] and not c["ok"]]
    if failures:
        print(f"\n{len(failures)} problema(s) crítico(s).", file=sys.stderr)
        return 1
    print("\nEntorno listo.")
    return 0


def cmd_set_status(args: argparse.Namespace) -> int:
    folder = cv.set_application_status(
        args.application,
        args.status,
        sent_date=args.sent_date,
    )
    print(f"OK {cv.relative(folder)} -> {args.status}")
    return 0


def cmd_sync_skills(args: argparse.Namespace) -> int:
    report = cv.sync_skills(
        targets=args.target,
        copy=args.copy,
        check_only=args.check,
        force=args.force,
    )
    for target, info in report["targets"].items():
        state = "OK   " if info["ok"] else "FALLA"
        print(f"{state} {target}: {info['created']} creadas, {len(info['missing'])} pendientes")
        for name in info["missing"]:
            print(f"      - {name}")

    if args.check and not report["ok"]:
        print("\nEjecuta `python3 scripts/cv.py sync-skills` para reparar.", file=sys.stderr)
        return 1
    return 0


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cv.py",
        description="Workspace CV-as-code: crear, renderizar y validar CVs con RenderCV.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="Crea .venv e instala dependencias")
    setup.add_argument("--no-skills", action="store_true", help="No enlazar skills de agentes")
    setup.set_defaults(func=cmd_setup)

    bootstrap = subparsers.add_parser(
        "bootstrap",
        help="Deja el workspace listo de una vez (idempotente, ideal para agentes)",
    )
    bootstrap.add_argument("--name", help="Crea main/cv.yaml con este nombre si falta")
    bootstrap.add_argument("--no-install", action="store_true", help="No instalar RenderCV")
    bootstrap.add_argument("--no-check", action="store_true", help="No validar los cv.yaml")
    bootstrap.add_argument("--pdf", action="store_true", help="Compila el PDF al validar")
    bootstrap.add_argument(
        "--json", action="store_true", help="Salida JSON (contrato para agentes)"
    )
    bootstrap.set_defaults(func=cmd_bootstrap)

    init = subparsers.add_parser("init", help="Crea main/cv.yaml desde el ejemplo")
    init.add_argument("--name", help="Reemplaza el nombre del CV de ejemplo")
    init.add_argument("--force", action="store_true", help="Sobrescribe main/cv.yaml")
    init.set_defaults(func=cmd_init)

    new = subparsers.add_parser("new", help="Crea una carpeta de postulación")
    new.add_argument("company", help="Empresa, ej. Banco BICE")
    new.add_argument("role", help="Rol, ej. Práctica Informática")
    new.add_argument("--url", default="", help="Link de la oferta")
    new.add_argument("--job-file", help="Archivo con la descripción de la oferta")
    new.add_argument("--date", default=cv.today(), help="Fecha base YYYY-MM-DD (default: hoy)")
    new.add_argument("--force", action="store_true", help="Sobrescribe archivos generados")
    new.set_defaults(func=cmd_new)

    render = subparsers.add_parser("render", help="Renderiza el CV maestro o una postulación")
    render.add_argument(
        "target",
        nargs="?",
        default="main",
        help="'main' o carpeta de applications/",
    )
    render.add_argument("--no-pdf", action="store_true", help="Genera solo Markdown/HTML")
    render.add_argument("--png", action="store_true", help="Genera también PNG")
    render.set_defaults(func=cmd_render)

    check = subparsers.add_parser("check", help="Valida todos los cv.yaml")
    check.add_argument("--pdf", action="store_true", help="Incluye la compilación del PDF")
    check.add_argument("--json", action="store_true", help="Salida JSON")
    check.set_defaults(func=cmd_check)

    listing = subparsers.add_parser("list", help="Lista postulaciones")
    listing.add_argument("--json", action="store_true", help="Salida JSON")
    listing.set_defaults(func=cmd_list)

    status = subparsers.add_parser("status", help="Resumen del workspace")
    status.add_argument("--json", action="store_true", help="Salida JSON")
    status.set_defaults(func=cmd_status)

    doctor = subparsers.add_parser("doctor", help="Diagnostica el entorno")
    doctor.add_argument("--json", action="store_true", help="Salida JSON")
    doctor.set_defaults(func=cmd_doctor)

    set_status = subparsers.add_parser("set-status", help="Actualiza el estado de una postulación")
    set_status.add_argument("application", help="Carpeta dentro de applications/")
    set_status.add_argument("status", help="draft, applied, interview, offer, rejected...")
    set_status.add_argument("--sent-date", help="Fecha de envío YYYY-MM-DD")
    set_status.set_defaults(func=cmd_set_status)

    skills = subparsers.add_parser("sync-skills", help="Enlaza skills a directorios de agentes")
    skills.add_argument(
        "--target",
        action="append",
        help="Directorio destino, ej. .claude/skills (repetible; default: .claude/skills)",
    )
    skills.add_argument("--copy", action="store_true", help="Copiar en vez de enlazar")
    skills.add_argument("--check", action="store_true", help="Solo verificar")
    skills.add_argument("--force", action="store_true", help="Reemplazar enlaces existentes")
    skills.set_defaults(func=cmd_sync_skills)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except cv.CvError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as exc:
        print(f"ERROR: tiempo agotado ejecutando {exc.cmd}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
