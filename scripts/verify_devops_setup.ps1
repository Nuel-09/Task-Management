# Quick verification script for local DevOps setup
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== Python tests + coverage =="
python -m pytest tests -v --cov=app --cov-fail-under=70

Write-Host "`n== Docker compose overlays =="
docker compose -f docker-compose.yml -f docker-compose.dev.yml config | Out-Null
docker compose -f docker-compose.yml -f docker-compose.staging.yml config | Out-Null
docker compose -f docker-compose.yml -f docker-compose.prod.yml config | Out-Null
Write-Host "Compose files are valid."

Write-Host "`n== Health checks =="
foreach ($port in @(8000, 8001, 8002)) {
    $resp = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing
    Write-Host "localhost:$port/health -> $($resp.StatusCode)"
}

Write-Host "`n== GitHub CLI auth =="
gh auth status

Write-Host "`n== GitHub environments =="
gh api repos/Nuel-09/Task-Management/environments --jq '.environments[].name'

Write-Host "`nSetup verification complete."
