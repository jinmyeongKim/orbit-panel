# Fill the winget manifest templates with a release version and the SHA256 of the built EXE.
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools/make_winget_manifests.ps1 -Version 1.2.0
# Output: packaging/winget/out/<Version>/  (ready to copy into a winget-pkgs fork)
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$ExePath = "dist/Orbit Panel.exe"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$templateDir = Join-Path $root "packaging/winget"
$outDir = Join-Path $templateDir "out/$Version"

if (-not (Test-Path (Join-Path $root $ExePath))) {
    throw "Built EXE not found at '$ExePath'. Run tools/build_release.ps1 first."
}

$sha256 = (Get-FileHash -Algorithm SHA256 (Join-Path $root $ExePath)).Hash

New-Item -ItemType Directory -Force $outDir | Out-Null

Get-ChildItem $templateDir -Filter "JinmyeongKim.OrbitPanel*.yaml" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace "<VERSION>", $Version -replace "<SHA256>", $sha256
    # Drop the template comment header lines.
    $content = ($content -split "`n" | Where-Object { $_ -notmatch "^#" }) -join "`n"
    Set-Content -Path (Join-Path $outDir $_.Name) -Value $content.TrimStart() -Encoding utf8
}

Write-Host "Manifests written to $outDir"
Write-Host "SHA256: $sha256"
Write-Host "Validate with: winget validate --manifest `"$outDir`""
