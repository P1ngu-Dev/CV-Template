#!/usr/bin/env bash
set -euo pipefail

rendercv render main/cv.yaml --dont-generate-pdf --dont-generate-png --output-folder /tmp/rendercv-main-check >/dev/null

declare -i checked=0
while IFS= read -r -d '' cv_file; do
  app_dir="$(dirname "$cv_file")"
  out_dir="/tmp/rendercv-check-${app_dir//\//-}"
  rendercv render "$cv_file" --dont-generate-pdf --dont-generate-png --output-folder "$out_dir" >/dev/null
  checked+=1
done < <(find applications -mindepth 2 -maxdepth 2 -name cv.yaml -print0 2>/dev/null)

echo "OK: main/cv.yaml válido; CVs de applications validados: $checked"
