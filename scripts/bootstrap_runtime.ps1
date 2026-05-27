# HookClose AI Runtime Bootstrap
Write-Host "Starting HookClose AI Runtime..."

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host "Starting data services..."
docker compose up -d postgres redis

Start-Sleep -Seconds 10

Write-Host "Initializing database..."
python scripts/init_db.py

Write-Host "Starting runtime services..."
docker compose up -d scheduler workflow-engine opencode-worker

Write-Host "Checking runtime health..."
Start-Sleep -Seconds 3
docker compose ps

Write-Host "HookClose Runtime Started."
