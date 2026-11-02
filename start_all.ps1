# Script khởi chạy đồng thời Backend (FastAPI :8000) và Frontend (Vite :5173) cho PharmaMind AI
$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   PHARMAMIND AI - KHOI CHAY TOAN BO HE THONG        " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Kiểm tra & cập nhật Database Migration (Alembic)..." -ForegroundColor Yellow
& "$RootDir\.venv\Scripts\alembic.exe" -c "$RootDir\backend\alembic.ini" upgrade head

Write-Host "`n[2/3] Khởi động Backend FastAPI tại http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir'; .\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "[3/3] Khởi động Frontend React + 3D Digital Twin tại http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootDir\frontend'; npm run dev"

Write-Host "`n✅ Hệ thống đã được khởi chạy!" -ForegroundColor Cyan
Write-Host "👉 Giao diện Web & Digital Twin 3D: http://localhost:5173" -ForegroundColor White
Write-Host "👉 Tài liệu Swagger API Backend   : http://localhost:8000/docs" -ForegroundColor White

