@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Installing build dependencies...
python -m pip install -r requirement.ini
if errorlevel 1 (
  echo Failed to install dependencies.
  exit /b 1
)

echo [2/3] Cleaning old build outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/3] Building Windows package...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name py_pctv ^
  --icon icon.ico ^
  --exclude-module PyQt5 ^
  --exclude-module PyQt6 ^
  --exclude-module PySide2 ^
  --exclude-module PySide6 ^
  --exclude-module matplotlib ^
  --exclude-module pandas ^
  --exclude-module scipy ^
  --add-data "icon.ico;." ^
  --add-data "static;static" ^
  --add-data "config.json;." ^
  py_pctv.py

if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo Build complete: dist\py_pctv\py_pctv.exe
echo You can run this EXE directly without installing Python.
exit /b 0
