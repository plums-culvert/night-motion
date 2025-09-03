#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
shopt -s nullglob nocaseglob

# --- 0) Deactivate any active venv (if present) ---
if [[ "${VIRTUAL_ENV:-}" != "" ]]; then
  deactivate || true
fi

# --- 1) Locate a source video; convert to MP4 if needed ---
first_video() {
  local vids=( *.mp4 *.mov *.m4v *.mkv *.avi *.webm )
  [[ ${#vids[@]} -gt 0 ]] && printf '%s\n' "${vids[0]}" || return 1
}

SRC="$(first_video)" || { echo "No video files found in $(pwd)"; exit 1; }

if [[ "$SRC" != "input.mp4" ]]; then
  ext="${SRC##*.}"
  ext_lc="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"
  if [[ "$ext_lc" == "mp4" ]]; then
    cp -f "$SRC" input.mp4
  else
    ffmpeg -y -hide_banner -loglevel error -i "$SRC" -c:v libx264 -crf 18 -preset fast -c:a copy input.mp4
  fi
fi

# --- 2) Crop top 36% ---
ffmpeg -y -hide_banner -loglevel error \
  -i input.mp4 \
  -vf "crop=in_w:in_h*0.36:0:0" \
  -c:v libx264 -crf 18 -preset fast -c:a copy output.mp4

# --- 3) Extract frames at 24 fps ---
mkdir -p frames annotated cropped composite_out
rm -f frames/*.png annotated/*.png cropped/*.png composite_out/*.png || true

ffmpeg -y -hide_banner -loglevel error \
  -i output.mp4 \
  -vf "fps=24" \
  "frames/frame_%05d.png"

# --- 4) venv + deps ---
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install opencv-python numpy

# --- 5) Run detectors/composites ---
python detect_night_lights.py
python composite_lights.py
python heatmap_cluster_crops.py
