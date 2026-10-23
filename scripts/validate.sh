#!/usr/bin/env bash
# Alias compatible de `python3 scripts/cv.py check`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/cv.py" check "$@"
