# HookClose AI Runtime Bootstrap

Write-Host "Starting HookClose AI Runtime..."

docker compose up -d postgres redis

Start-Sleep -Seconds 10

Write-Host "Initializing database..."

python scripts/init_db.py

Write-Host "Starting workflow runtime..."

docker compose up -d workflow-engine

Write-Host "Starting scheduler..."

docker compose up -d scheduler

Write-Host "Starting workers..."

docker compose up -d opencode-worker
docker compose up -d review-worker
docker compose up -d repair-worker

Write-Host "Checking runtime health..."

docker ps

Write-Host "HookClose Runtime Started."
