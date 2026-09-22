$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --quiet -e ".[build]"
& .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name CodeTypingStudio main.py
