# ThreatLens AI - Stop Script
# Run this script to stop all services

Write-Host "🛑 Stopping ThreatLens AI..." -ForegroundColor Yellow
Write-Host ""

# Stop backend processes
Write-Host "Stopping FastAPI server..." -ForegroundColor Gray
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*ThreatLens*"} | Stop-Process -Force

# Stop frontend processes
Write-Host "Stopping frontend dev server..." -ForegroundColor Gray
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*vite*"} | Stop-Process -Force

# Stop Docker services
Write-Host "Stopping Docker services..." -ForegroundColor Gray
Set-Location backend
docker-compose down

Write-Host ""
Write-Host "✅ All services stopped" -ForegroundColor Green
Write-Host ""
Write-Host "To remove all data (reset): docker-compose down -v" -ForegroundColor Yellow
