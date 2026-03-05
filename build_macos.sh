#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[0/3] Generating icon.icns (if icon.ico exists)..."
if [[ -f "icon.ico" ]]; then
  python3 - <<'PY'
import os
import shutil
import tempfile
from PIL import Image
from icnsutil import IcnsFile

ico_path = "icon.ico"
out_icns = "icon.icns"
out_template = "icon_template.png"

img = Image.open(ico_path)

best = None
best_size = 0
try:
    for frame in range(getattr(img, "n_frames", 1)):
        img.seek(frame)
        w, h = img.size
        if w == h and w > best_size:
            best = img.copy().convert("RGBA")
            best_size = w
except Exception:
    pass

if best is None:
    best = img.convert("RGBA")

entries = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]

tmp_dir = tempfile.mkdtemp(prefix="iconset-")
try:
    for name, size in entries:
        out = best.resize((size, size), Image.LANCZOS)
        out.save(os.path.join(tmp_dir, name), format="PNG")

    icns = IcnsFile()
    for name, _ in entries:
        icns.add_media(file=os.path.join(tmp_dir, name))
    icns.write(out_icns)

    # Generate a monochrome template icon for macOS menu bar
    base = best.resize((32, 32), Image.LANCZOS)
    base = base.convert("RGBA")
    r, g, b, a = base.split()
    black = Image.new("RGBA", base.size, (0, 0, 0, 255))
    template = Image.composite(black, Image.new("RGBA", base.size, (0, 0, 0, 0)), a)
    template.save(out_template, format="PNG")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
PY
fi

echo "[1/3] Installing build dependencies..."
python3 -m pip install -r requirement.ini

echo "[2/3] Cleaning old build outputs..."
rm -rf build dist

ICON_ARG=()
if [[ -f "icon.icns" ]]; then
  ICON_ARG=(--icon "icon.icns")
fi

echo "[3/3] Building macOS package..."
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name py_pctv \
  "${ICON_ARG[@]}" \
  --exclude-module PyQt5 \
  --exclude-module PyQt6 \
  --exclude-module PySide2 \
  --exclude-module PySide6 \
  --exclude-module matplotlib \
  --exclude-module pandas \
  --exclude-module scipy \
  --add-data "icon.ico:." \
  --add-data "icon.icns:." \
  --add-data "icon_template.png:." \
  --add-data "static:static" \
  --add-data "config.json:." \
  py_pctv.py

echo "Build complete: dist/py_pctv.app"
