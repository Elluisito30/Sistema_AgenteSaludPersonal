# Desarrollo local: solo PostgreSQL en Docker; backend y frontend nativos.
# Uso: .\dev-local.ps1

Write-Host "==> PostgreSQL (Docker) en 127.0.0.1:5433" -ForegroundColor Cyan
docker compose up db -d

Write-Host ""
Write-Host "Terminal 1 - Backend:" -ForegroundColor Yellow
Write-Host '$env:PYTHONUTF8="1"; $env:PYTHONPATH="backend"; python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload'

Write-Host ""
Write-Host "Terminal 2 - Frontend:" -ForegroundColor Yellow
Write-Host "cd frontend-react; npm run dev"

Write-Host ""
Write-Host "URLs:" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:8501"
Write-Host "  Backend:  http://localhost:8000/docs"
