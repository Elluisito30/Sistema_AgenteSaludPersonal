# ============================================
# COMANDOS RÁPIDOS DOCKER - HEALTH AI
# ============================================

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   HEALTH AI - COMANDOS RÁPIDOS        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Menú de opciones
Write-Host "Selecciona una opción:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. 🚀 Desplegar/Iniciar servicios" -ForegroundColor Green
Write-Host "  2. 🔄 Reconstruir y desplegar" -ForegroundColor Yellow
Write-Host "  3. 🧹 Limpiar y reconstruir todo" -ForegroundColor Red
Write-Host "  4. 📋 Ver logs en vivo" -ForegroundColor Blue
Write-Host "  5. 📊 Ver estado de contenedores" -ForegroundColor Cyan
Write-Host "  6. ⏸️  Detener servicios" -ForegroundColor Magenta
Write-Host "  7. 🔁 Reiniciar servicios" -ForegroundColor Yellow
Write-Host "  8. 🔍 Ver logs del backend" -ForegroundColor Blue
Write-Host "  9. 🔍 Ver logs del frontend" -ForegroundColor Blue
Write-Host " 10. 🌐 Abrir aplicación en navegador" -ForegroundColor Green
Write-Host " 11. 🩺 Health check" -ForegroundColor Green
Write-Host "  0. ❌ Salir" -ForegroundColor Gray
Write-Host ""

$opcion = Read-Host "Opción"

switch ($opcion) {
    "1" {
        Write-Host "`n🚀 Iniciando servicios..." -ForegroundColor Green
        docker-compose up -d
        Write-Host "`n✅ Servicios iniciados" -ForegroundColor Green
        Write-Host "Frontend: http://localhost:8501" -ForegroundColor Cyan
        Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
    }
    "2" {
        Write-Host "`n🔄 Reconstruyendo..." -ForegroundColor Yellow
        .\deploy_docker.ps1 -Rebuild
    }
    "3" {
        Write-Host "`n🧹 Limpiando y reconstruyendo..." -ForegroundColor Red
        .\deploy_docker.ps1 -Clean -Rebuild
    }
    "4" {
        Write-Host "`n📋 Logs en vivo (Ctrl+C para salir)..." -ForegroundColor Blue
        docker-compose logs -f
    }
    "5" {
        Write-Host "`n📊 Estado de contenedores:" -ForegroundColor Cyan
        docker-compose ps
        Write-Host "`n💻 Uso de recursos:" -ForegroundColor Cyan
        docker stats --no-stream health-ai-backend health-ai-frontend
    }
    "6" {
        Write-Host "`n⏸️  Deteniendo servicios..." -ForegroundColor Magenta
        docker-compose down
        Write-Host "✅ Servicios detenidos" -ForegroundColor Green
    }
    "7" {
        Write-Host "`n🔁 Reiniciando servicios..." -ForegroundColor Yellow
        docker-compose restart
        Write-Host "✅ Servicios reiniciados" -ForegroundColor Green
    }
    "8" {
        Write-Host "`n🔍 Logs del Backend (Ctrl+C para salir)..." -ForegroundColor Blue
        docker-compose logs -f backend
    }
    "9" {
        Write-Host "`n🔍 Logs del Frontend (Ctrl+C para salir)..." -ForegroundColor Blue
        docker-compose logs -f frontend
    }
    "10" {
        Write-Host "`n🌐 Abriendo aplicación..." -ForegroundColor Green
        Start-Process "http://localhost:8501"
        Write-Host "También disponible:" -ForegroundColor Cyan
        Write-Host "  Backend API Docs: http://localhost:8000/docs" -ForegroundColor Gray
    }
    "11" {
        Write-Host "`n🩺 Verificando salud de los servicios..." -ForegroundColor Green
        Write-Host "`nBackend:" -ForegroundColor Yellow
        try {
            $backend = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3
            Write-Host "✅ Backend OK - Status: $($backend.status)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Backend no responde" -ForegroundColor Red
        }
        
        Write-Host "`nFrontend:" -ForegroundColor Yellow
        try {
            $frontend = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -TimeoutSec 3 -UseBasicParsing
            if ($frontend.StatusCode -eq 200) {
                Write-Host "✅ Frontend OK" -ForegroundColor Green
            }
        } catch {
            Write-Host "❌ Frontend no responde" -ForegroundColor Red
        }
        
        Write-Host "`nContenedores:" -ForegroundColor Yellow
        docker-compose ps
    }
    "0" {
        Write-Host "`n👋 ¡Hasta luego!" -ForegroundColor Gray
        exit
    }
    default {
        Write-Host "`n❌ Opción no válida" -ForegroundColor Red
    }
}

Write-Host ""
Read-Host "Presiona Enter para continuar"
