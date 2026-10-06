# P&ID Document Intelligence System - Startup Script
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " P&ID Document Intelligence System" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$Root = "c:\Users\abesh\OneDrive\Desktop\Mavericks"

New-Item -ItemType Directory -Force -Path "$Root\data\uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "$Root\data\processed" | Out-Null

Write-Host "[1/2] Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\backend'; py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting Vite frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\frontend'; npm.cmd run dev"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "  Frontend UI:  http://localhost:5173/" -ForegroundColor Green
Write-Host "  Backend API:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Start-Process "http://localhost:5173/"
