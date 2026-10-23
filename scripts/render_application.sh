#!/usr/bin/env bash
# Alias compatible de `python3 scripts/cv.py render <carpeta>`.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Uso: scripts/render_application.sh applications/YYYY-MM-empresa-rol" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/cv.py" render "${1%/}"
