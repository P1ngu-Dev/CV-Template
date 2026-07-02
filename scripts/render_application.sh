#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Uso: scripts/render_application.sh applications/YYYY-MM-empresa-rol" >&2
  exit 2
fi

APP_DIR="${1%/}"
CV_FILE="$APP_DIR/cv.yaml"
OUT_DIR="$APP_DIR/outputs"
ABS_OUT_DIR="$(pwd)/$OUT_DIR"

if [[ ! -f "$CV_FILE" ]]; then
  echo "No existe $CV_FILE" >&2
  exit 2
fi

mkdir -p "$ABS_OUT_DIR"
rendercv render "$CV_FILE" --output-folder "$ABS_OUT_DIR"

echo "Outputs generados en: $ABS_OUT_DIR"
