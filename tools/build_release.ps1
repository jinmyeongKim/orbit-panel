$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$iconPath = Join-Path $projectRoot "assets\icons\orbit_panel.ico"
$assetsData = "assets;assets"

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "Orbit Panel" `
  --icon $iconPath `
  --add-data $assetsData `
  main.py
