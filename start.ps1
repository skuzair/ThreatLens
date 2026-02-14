# ThreatLens AI - Quick Start Script
# Run this script to start the entire system

Write-Host "[ThreatLens] Starting ThreatLens AI..." -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if Docker Desktop is running
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and wait for it to fully initialize." -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Docker found and running" -ForegroundColor Green

# Start backend services
Write-Host ""
Write-Host "Starting backend services..." -ForegroundColor Yellow
Set-Location backend

Write-Host "Starting Docker Compose..." -ForegroundColor Gray
Write-Host "(First run may take several minutes to download images)" -ForegroundColor Gray
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to start Docker services" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "1. Check your internet connection" -ForegroundColor Gray
    Write-Host "2. Try again - Docker Hub may be experiencing issues" -ForegroundColor Gray
    Write-Host "3. Configure Docker to use a different registry mirror" -ForegroundColor Gray
    Write-Host "4. If behind a proxy, configure Docker proxy settings" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To retry: .\start.ps1" -ForegroundColor Cyan
    Write-Host "To clean up: cd backend; docker-compose down -v" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "[OK] Docker services started" -ForegroundColor Green
Write-Host "Waiting for services to initialize (30 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# Pull Ollama model
Write-Host ""
Write-Host "Setting up Ollama LLM..." -ForegroundColor Yellow
$ollamaCheck = docker exec threatlens-ollama ollama list 2>&1 | Select-String "mistral"
if (!$ollamaCheck) {
    Write-Host "Pulling Mistral-7B model (this may take a few minutes)..." -ForegroundColor Gray
    docker exec threatlens-ollama ollama pull mistral:7b
    Write-Host "[OK] Ollama model ready" -ForegroundColor Green
} else {
    Write-Host "[OK] Ollama model already installed" -ForegroundColor Green
}

# Setup Python environment
Write-Host ""
Write-Host "Setting up Python environment..." -ForegroundColor Yellow

$venvPath = "..\venv"
if (!(Test-Path $venvPath)) {
    Write-Host "[WARNING] Virtual environment not found at $venvPath" -ForegroundColor Yellow
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    Set-Location ..
    python -m venv venv
    Set-Location backend
}

Write-Host "[OK] Using virtual environment at $venvPath" -ForegroundColor Green

# Setup .env if not exists
if (!(Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Gray
    Copy-Item .env.example .env
    Write-Host "[WARNING] Please edit backend/.env with your configuration" -ForegroundColor Yellow
}

# Start FastAPI
Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
$pythonExe = Resolve-Path "..\venv\Scripts\python.exe"
Start-Process -FilePath $pythonExe -ArgumentList "main.py" -WorkingDirectory (Get-Location)
Start-Sleep -Seconds 5

# Check if API is up
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "[OK] Backend API started at http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Backend API may still be starting..." -ForegroundColor Yellow
}

# Start frontend
Set-Location ../frontend/threat_lens_frontend
Write-Host ""
Write-Host "Setting up frontend..." -ForegroundColor Yellow

if (!(Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Gray
    npm install
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install Node.js dependencies" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[OK] Node.js dependencies ready" -ForegroundColor Green

Write-Host ""
Write-Host "Starting frontend dev server..." -ForegroundColor Yellow
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory (Get-Location)

Start-Sleep -Seconds 5

# Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "[OK] ThreatLens AI is starting up!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend:         http://localhost:3000" -ForegroundColor White
Write-Host "Backend API:      http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:         http://localhost:8000/docs" -ForegroundColor White
Write-Host "MinIO Console:    http://localhost:9001" -ForegroundColor White
Write-Host "Neo4j Browser:    http://localhost:7474" -ForegroundColor White
Write-Host ""
Write-Host "Service Credentials:" -ForegroundColor Yellow
Write-Host "  PostgreSQL: admin / threatlens123" -ForegroundColor Gray
Write-Host "  MinIO:      minioadmin / minioadmin123" -ForegroundColor Gray
Write-Host "  Neo4j:      neo4j / threatlens123" -ForegroundColor Gray
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop services" -ForegroundColor Yellow
Write-Host "To stop all Docker services: docker-compose down" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "[ThreatLens] System is ready!" -ForegroundColor Green
