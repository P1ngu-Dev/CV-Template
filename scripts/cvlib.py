"""Núcleo del workspace CV, sin dependencias de terceros.

Lo usan tanto el CLI (`scripts/cv.py`) como el servidor MCP
(`mcp/cv_workspace_server.py`), de modo que ambos se comportan igual.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_DIR = ROOT / "main"
MASTER_CV = MAIN_DIR / "cv.yaml"
EXAMPLE_CV = MAIN_DIR / "example_cv.yaml"
APPLICATIONS_DIR = ROOT / "applications"
TEMPLATES_DIR = ROOT / "templates"
OUTPUTS_DIRNAME = "outputs"

MIN_PYTHON = (3, 12)
PINNED_RENDERCV = "2.8"

APPLICATION_TEMPLATES = (
    "application_readme.md",
    "job_description.md",
    "analysis.md",
    "application_log.md",
    "cover_letter.md",
)

PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


class CvError(RuntimeError):
    """Error esperado del workspace, con un mensaje accionable."""


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------


def today() -> str:
    return dt.date.today().isoformat()


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", value)[:80] or "postulacion"


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_text(path: Path, content: str, *, force: bool = False) -> None:
    if path.exists() and not force:
        raise CvError(
            f"Ya existe {relative(path)}. Usa --force para sobrescribir archivos generados."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run(
    cmd: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 900,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


# --------------------------------------------------------------------------
# RenderCV
# --------------------------------------------------------------------------


def _venv_binary(name: str) -> Path | None:
    for folder in ("bin", "Scripts"):
        for suffix in ("", ".exe", ".cmd"):
            candidate = ROOT / ".venv" / folder / f"{name}{suffix}"
            if candidate.exists():
                return candidate
    return None


def rendercv_command() -> list[str]:
    """Resuelve el ejecutable de RenderCV de forma portable.

    Orden: variable RENDERCV, `.venv` del repo, PATH.
    """
    override = os.environ.get("RENDERCV")
    if override:
        return [override]

    local = _venv_binary("rendercv")
    if local:
        return [str(local)]

    found = shutil.which("rendercv")
    if found:
        return [found]

    raise CvError(
        "RenderCV no está instalado (o no está en el PATH).\n"
        "  Opción 1: python3 scripts/cv.py setup\n"
        "  Opción 2: pipx install 'rendercv[full]==2.8'"
    )


def rendercv_version() -> str:
    try:
        proc = run(rendercv_command() + ["--version"], timeout=60)
    except (CvError, OSError, subprocess.SubprocessError):
        return "desconocida"

    output = (proc.stdout or proc.stderr).strip()
    if proc.returncode == 0 and output:
        return output.splitlines()[0].strip()
    return "desconocida"


def render_cv(
    cv_file: Path,
    out_dir: Path,
    *,
    pdf: bool = True,
    png: bool = False,
    html: bool = True,
    markdown: bool = True,
    timeout: int = 900,
) -> dict[str, object]:
    cv_file = Path(cv_file)
    if not cv_file.exists():
        raise CvError(f"No existe el CV: {relative(cv_file)}")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = rendercv_command() + [
        "render",
        str(cv_file),
        "--output-folder",
        str(out_dir),
    ]
    if not pdf:
        cmd.append("--dont-generate-pdf")
    if not png:
        cmd.append("--dont-generate-png")
    if not html:
        cmd.append("--dont-generate-html")
    if not markdown:
        cmd.append("--dont-generate-markdown")

    proc = run(cmd, timeout=timeout)
    return {
        "ok": proc.returncode == 0,
        "command": " ".join(cmd),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "output": relative(out_dir),
    }


def output_dir_for(cv_file: Path) -> Path:
    cv_file = Path(cv_file).resolve()
    if cv_file == MASTER_CV.resolve():
        return MAIN_DIR / OUTPUTS_DIRNAME
    if cv_file.parent.parent == APPLICATIONS_DIR.resolve():
        return cv_file.parent / OUTPUTS_DIRNAME
    return cv_file.parent / OUTPUTS_DIRNAME


def resolve_cv(target: str) -> Path:
    """Acepta 'main', un nombre de carpeta en applications/ o una ruta YAML."""
    value = (target or "main").strip()

    if value.lower() in {"main", "master", "maestro", "cv"}:
        if MASTER_CV.exists():
            return MASTER_CV
        raise CvError(
            "No existe main/cv.yaml. Créalo con:\n"
            "  python3 scripts/cv.py init --name \"Tu Nombre\""
        )

    candidate = Path(value)
    options = [candidate, ROOT / candidate]
    for option in options:
        if option.is_file() and option.suffix in {".yaml", ".yml"}:
            return option.resolve()
        if option.is_dir() and (option / "cv.yaml").exists():
            return (option / "cv.yaml").resolve()

    app = APPLICATIONS_DIR / value
    if (app / "cv.yaml").exists():
        return (app / "cv.yaml").resolve()

    raise CvError(
        f"No encontré un cv.yaml para '{target}'.\n"
        "Usa 'main', el nombre de una carpeta de applications/ o una ruta a un .yaml."
    )


# --------------------------------------------------------------------------
# Plantillas y postulaciones
# --------------------------------------------------------------------------


def render_template(template_name: str, context: dict[str, str]) -> str:
    path = TEMPLATES_DIR / template_name
    if not path.exists():
        raise CvError(f"Falta la plantilla {relative(path)}.")
    text = path.read_text(encoding="utf-8")
    return PLACEHOLDER_RE.sub(lambda m: context.get(m.group(1), m.group(0)), text)


def missing_templates() -> list[str]:
    return [name for name in APPLICATION_TEMPLATES if not (TEMPLATES_DIR / name).exists()]


def init_master(*, name: str | None = None, force: bool = False) -> Path:
    if MASTER_CV.exists() and not force:
        raise CvError(
            f"Ya existe {relative(MASTER_CV)}. Usa --force solo si quieres reemplazarlo."
        )
    if not EXAMPLE_CV.exists():
        raise CvError(f"Falta el CV de ejemplo: {relative(EXAMPLE_CV)}.")

    text = EXAMPLE_CV.read_text(encoding="utf-8")
    if name:
        text = re.sub(
            r'(?m)^(\s*name:\s*)"[^"]*"',
            lambda m: f'{m.group(1)}"{name}"',
            text,
            count=1,
        )
    write_text(MASTER_CV, text, force=True)
    return MASTER_CV


def create_application(
    company: str,
    role: str,
    *,
    url: str = "",
    job_text: str = "",
    date: str | None = None,
    force: bool = False,
) -> Path:
    company, role = company.strip(), role.strip()
    if not company or not role:
        raise CvError("Empresa y rol son obligatorios.")

    if not MASTER_CV.exists():
        raise CvError(
            "No existe main/cv.yaml (fuente de verdad). Créalo primero con:\n"
            "  python3 scripts/cv.py init --name \"Tu Nombre\""
        )

    date_str = (date or today()).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        raise CvError(f"Fecha inválida '{date_str}'. Usa el formato YYYY-MM-DD.")

    folder = APPLICATIONS_DIR / f"{date_str[:7]}-{slugify(company)}-{slugify(role)}"
    folder.mkdir(parents=True, exist_ok=True)

    context = {
        "COMPANY": company,
        "ROLE": role,
        "DATE": date_str,
        "URL": url.strip(),
        "URL_OR_PENDING": url.strip() or "Pendiente",
        "JOB_TEXT": job_text.strip()
        or "Pegar aquí la oferta original o un resumen fiel.",
        "FOLDER_NAME": folder.name,
    }

    generated = {
        "README.md": "application_readme.md",
        "job_description.md": "job_description.md",
        "analysis.md": "analysis.md",
        "application_log.md": "application_log.md",
        "cover_letter.md": "cover_letter.md",
    }
    for output_name, template_name in generated.items():
        write_text(
            folder / output_name,
            render_template(template_name, context),
            force=force,
        )

    outputs = folder / OUTPUTS_DIRNAME
    outputs.mkdir(exist_ok=True)
    keep = outputs / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")

    shutil.copyfile(MASTER_CV, folder / "cv.yaml")
    return folder


def _section(text: str, title: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(title)}\s*$\n(.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    body = match.group(1).strip()
    return body.splitlines()[0].strip() if body else ""


def _set_section(text: str, title: str, value: str) -> str:
    pattern = re.compile(
        rf"(^##\s+{re.escape(title)}\s*$\n)(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if pattern.search(text):
        return pattern.sub(
            lambda m: f"{m.group(1)}\n{value}\n\n",
            text,
            count=1,
        )
    return text.rstrip() + f"\n\n## {title}\n\n{value}\n"


def list_applications() -> list[dict[str, object]]:
    if not APPLICATIONS_DIR.exists():
        return []

    results: list[dict[str, object]] = []
    for folder in sorted(APPLICATIONS_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        log_file = folder / "application_log.md"
        log_text = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
        outputs_dir = folder / OUTPUTS_DIRNAME
        outputs = (
            sorted(p.name for p in outputs_dir.iterdir() if p.is_file())
            if outputs_dir.exists()
            else []
        )

        results.append(
            {
                "folder": folder.name,
                "company": _section(log_text, "Empresa") or "—",
                "role": _section(log_text, "Rol") or "—",
                "status": _section(log_text, "Estado") or "draft",
                "sent": _section(log_text, "Fecha de envío") or "Pendiente",
                "has_cv": (folder / "cv.yaml").exists(),
                "outputs": outputs,
            }
        )
    return results


def resolve_application(value: str) -> Path:
    candidate = Path(value)
    for option in (candidate, ROOT / candidate, APPLICATIONS_DIR / value):
        if option.is_dir() and (option / "cv.yaml").exists():
            return option.resolve()
        if option.is_dir() and (option / "application_log.md").exists():
            return option.resolve()
    raise CvError(f"No encontré la postulación '{value}' dentro de applications/.")


def set_application_status(application: str, status: str, *, sent_date: str | None = None) -> Path:
    folder = resolve_application(application)
    status = status.strip()
    if not status:
        raise CvError("El estado no puede estar vacío.")

    log_file = folder / "application_log.md"
    if not log_file.exists():
        raise CvError(f"Falta {relative(log_file)}.")

    text = log_file.read_text(encoding="utf-8")
    text = _set_section(text, "Estado", status)
    if sent_date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", sent_date):
            raise CvError("La fecha de envío debe tener formato YYYY-MM-DD.")
        text = _set_section(text, "Fecha de envío", sent_date)
    log_file.write_text(text, encoding="utf-8")

    readme = folder / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
        readme.write_text(_set_section(readme_text, "Estado", status), encoding="utf-8")

    return folder


# --------------------------------------------------------------------------
# Validación y estado
# --------------------------------------------------------------------------


@dataclass
class CheckResult:
    target: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _compact_error(payload: dict[str, object], limit: int = 12) -> str:
    text = "\n".join(
        part
        for part in (str(payload.get("stderr") or ""), str(payload.get("stdout") or ""))
        if part
    ).strip()
    if not text:
        return "RenderCV falló sin salida."
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines[-limit:])


def check_all(*, pdf: bool = False) -> list[CheckResult]:
    targets: list[tuple[str, Path]] = []
    if MASTER_CV.exists():
        targets.append((relative(MASTER_CV), MASTER_CV))
    if EXAMPLE_CV.exists():
        targets.append((relative(EXAMPLE_CV), EXAMPLE_CV))
    for cv_file in sorted(APPLICATIONS_DIR.glob("*/cv.yaml")):
        targets.append((relative(cv_file), cv_file))

    if not targets:
        raise CvError("No hay archivos cv.yaml para validar.")

    results: list[CheckResult] = []
    for label, cv_file in targets:
        with tempfile.TemporaryDirectory(prefix="cv-check-") as tmp:
            payload = render_cv(
                cv_file,
                Path(tmp),
                pdf=pdf,
                png=False,
                html=False,
                markdown=False,
            )
        results.append(
            CheckResult(
                target=label,
                ok=bool(payload["ok"]),
                detail="" if payload["ok"] else _compact_error(payload),
            )
        )
    return results


def status() -> dict[str, object]:
    try:
        command: list[str] | None = rendercv_command()
        version = rendercv_version()
    except CvError:
        command = None
        version = "no instalado"

    skills_source = ROOT / ".agents" / "skills"
    skills = sorted(p.parent.name for p in skills_source.glob("*/SKILL.md"))

    return {
        "root": str(ROOT),
        "python": sys.version.split()[0],
        "rendercv": {
            "found": command is not None,
            "version": version,
            "command": " ".join(command) if command else None,
        },
        "master_cv": {"path": "main/cv.yaml", "exists": MASTER_CV.exists()},
        "applications": len(list_applications()),
        "skills": {
            "installed": len(skills),
            "lockfile": (ROOT / "skills-lock.json").exists(),
        },
        "agents": {
            "agents_md": (ROOT / "AGENTS.md").exists(),
            "mcp_server": (ROOT / "mcp" / "cv_workspace_server.py").exists(),
        },
    }


# --------------------------------------------------------------------------
# Skills para agentes
# --------------------------------------------------------------------------

SKILLS_SOURCE = ROOT / ".agents" / "skills"
DEFAULT_AGENT_TARGETS = (".claude/skills",)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _same_tree(left: Path, right: Path) -> bool:
    """Compara dos carpetas pequeñas por ruta relativa y contenido."""

    def snapshot(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    try:
        return snapshot(left) == snapshot(right)
    except OSError:
        return False


def _is_synced(source: Path, destination: Path) -> bool:
    if not destination.exists() and not destination.is_symlink():
        return False
    if destination.is_symlink():
        return destination.resolve() == source.resolve()
    return _same_tree(source, destination)


def sync_skills(
    targets: list[str] | None = None,
    *,
    copy: bool = False,
    check_only: bool = False,
    force: bool = False,
) -> dict[str, object]:
    """Enlaza .agents/skills en los directorios que cada agente escanea.

    `.agents/skills` es la fuente única. OpenCode la lee directamente; Claude Code
    necesita `.claude/skills`.
    """
    if not SKILLS_SOURCE.exists():
        raise CvError(
            "No existe .agents/skills. Restaura las skills con:\n"
            "  npx skills experimental_install"
        )

    skills = sorted(p.parent.name for p in SKILLS_SOURCE.glob("*/SKILL.md"))
    if not skills:
        raise CvError("No hay skills instaladas en .agents/skills.")

    report: dict[str, object] = {
        "skills": len(skills),
        "targets": {},
        "ok": True,
    }

    for target in targets or list(DEFAULT_AGENT_TARGETS):
        target_dir = ROOT / target
        missing: list[str] = []
        created = 0

        for name in skills:
            source = SKILLS_SOURCE / name
            destination = target_dir / name

            if check_only:
                if _is_synced(source, destination):
                    continue
                missing.append(name)
                continue

            if destination.exists() or destination.is_symlink():
                if _is_synced(source, destination):
                    continue
                if not force:
                    missing.append(name)
                    continue
                _remove_path(destination)

            target_dir.mkdir(parents=True, exist_ok=True)
            if copy:
                shutil.copytree(source, destination)
            else:
                try:
                    destination.symlink_to(
                        os.path.relpath(source, target_dir),
                        target_is_directory=True,
                    )
                except OSError:
                    # Windows sin permisos de symlink: se copia para no romper el flujo.
                    shutil.copytree(source, destination)
            created += 1

        ok = not missing
        report["targets"][target] = {
            "ok": ok,
            "created": created,
            "missing": missing,
        }
        if not ok:
            report["ok"] = False

    return report


# --------------------------------------------------------------------------
# Diagnóstico
# --------------------------------------------------------------------------


def doctor() -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "", *, required: bool = True) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "required": required})

    add(
        "Python >= 3.12",
        sys.version_info >= MIN_PYTHON,
        f"Python {sys.version.split()[0]} en {sys.executable}",
    )

    try:
        command = rendercv_command()
        version = rendercv_version()
        add(
            "RenderCV disponible",
            True,
            f"{' '.join(command)} (versión {version})",
        )
        add(
            f"RenderCV {PINNED_RENDERCV}",
            PINNED_RENDERCV in version,
            f"versión detectada: {version}",
            required=False,
        )
    except CvError as exc:
        add("RenderCV disponible", False, str(exc).splitlines()[0])

    add(
        "CV maestro",
        MASTER_CV.exists(),
        relative(MASTER_CV) if MASTER_CV.exists() else "falta: ejecuta `cv.py init`",
        required=False,
    )
    missing = missing_templates()
    add(
        "Plantillas",
        not missing,
        "todas presentes" if not missing else f"faltan: {', '.join(missing)}",
    )
    add(
        "AGENTS.md",
        (ROOT / "AGENTS.md").exists(),
        "instrucciones canónicas para agentes",
    )
    add(
        "Servidor MCP",
        (ROOT / "mcp" / "cv_workspace_server.py").exists(),
        "mcp/cv_workspace_server.py",
    )
    add(
        "Lockfile de skills",
        (ROOT / "skills-lock.json").exists(),
        "skills-lock.json en la raíz (canónico)",
    )
    add(
        "Sin lockfile duplicado",
        not (SKILLS_SOURCE / "skills-lock.json").exists(),
        ".agents/skills/skills-lock.json no debe existir",
        required=False,
    )

    skills = sorted(p.parent.name for p in SKILLS_SOURCE.glob("*/SKILL.md"))
    add("Skills instaladas", bool(skills), f"{len(skills)} skills en .agents/skills")

    links = ROOT / ".claude" / "skills"
    linked = len(list(links.glob("*/SKILL.md"))) if links.exists() else 0
    add(
        "Enlaces para Claude Code",
        linked >= len(skills) and bool(skills),
        f"{linked}/{len(skills)} (ejecuta `cv.py sync-skills`)",
        required=False,
    )

    return checks
