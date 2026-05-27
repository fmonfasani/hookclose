# =============================================================================
# AINE - local bootstrap (Windows / PowerShell).
# =============================================================================
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "[aine] checking prerequisites..."
foreach ($bin in @("python", "docker")) {
    if (-not (Get-Command $bin -ErrorAction SilentlyContinue)) {
        Write-Error "[aine] missing dependency: $bin"
        exit 1
    }
}

if (-not (Test-Path ".env")) {
    Write-Host "[aine] creating .env from .env.example"
    Copy-Item ".env.example" ".env"
}

if (-not (Test-Path ".venv")) {
    Write-Host "[aine] creating virtualenv at .venv"
    python -m venv .venv
}

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
& $venvPython -m pip install -U pip wheel
& $venvPython -m pip install -e ".[dev]"

Write-Host "[aine] starting docker compose stack..."
docker compose up -d --build

Write-Host "[aine] bootstrap complete."
Write-Host "  api:    http://localhost:8000/health"
Write-Host "  flower: http://localhost:5555"
Write-Host "  jaeger: http://localhost:16686"
