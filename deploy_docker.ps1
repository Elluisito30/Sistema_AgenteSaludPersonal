# ============================================
# SCRIPT DE DESPLIEGUE DOCKER - HEALTH AI
# ============================================
# Uso: .\deploy_docker.ps1 [opciones]
# Opciones:
#   -Rebuild    : Reconstruir imágenes desde cero
#   -Clean      : Limpiar contenedores y volúmenes antiguos
#   -Logs       : Ver logs después del despliegue
# ============================================

param(
    [switch]$Rebuild,
    [switch]$Clean,
    [switch]$Logs
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  HEALTH AI - DESPLIEGUE DOCKER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Docker está corriendo
Write-Host "[1/6] Verificando Docker..." -ForegroundColor Yellow
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker no está corriendo. Por favor inicia Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker está activo" -ForegroundColor Green
Write-Host ""

# Limpiar contenedores antiguos si se solicita
if ($Clean) {
    Write-Host "[2/6] Limpiando contenedores y volúmenes antiguos..." -ForegroundColor Yellow
    docker-compose down -v
    docker system prune -f
    Write-Host "✅ Limpieza completada" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[2/6] Deteniendo contenedores existentes..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Contenedores detenidos" -ForegroundColor Green
    Write-Host ""
}

# Construir imágenes
if ($Rebuild) {
    Write-Host "[3/6] Reconstruyendo imágenes (--no-cache)..." -ForegroundColor Yellow
    docker-compose build --no-cache
} else {
    Write-Host "[3/6] Construyendo imágenes..." -ForegroundColor Yellow
    docker-compose build
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al construir las imágenes" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Imágenes construidas" -ForegroundColor Green
Write-Host ""

# Iniciar servicios
Write-Host "[4/6] Iniciando servicios..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al iniciar los servicios" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Servicios iniciados" -ForegroundColor Green
Write-Host ""

# Esperar a que los servicios estén listos
Write-Host "[5/6] Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar estado de los contenedores
Write-Host "[6/6] Verificando estado de los contenedores..." -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Verificar salud del backend
Write-Host "Verificando salud del backend..." -ForegroundColor Yellow
$backendHealth = $null
$maxRetries = 10
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($backendHealth) {
            Write-Host "✅ Backend está respondiendo correctamente" -ForegroundColor Green
            break
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "Reintentando... ($retryCount/$maxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds 3
        }
    }
}

if (-not $backendHealth) {
    Write-Host "⚠️ El backend no responde, pero puede estar iniciando. Verifica los logs." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ✅ DESPLIEGUE COMPLETADO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 URLs de acceso:" -ForegroundColor White
Write-Host "   Frontend:  http://localhost:8501" -ForegroundColor Cyan
Write-Host "   Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Comandos útiles:" -ForegroundColor White
Write-Host "   Ver logs:           docker-compose logs -f" -ForegroundColor Gray
Write-Host "   Ver logs backend:   docker-compose logs -f backend" -ForegroundColor Gray
Write-Host "   Ver logs frontend:  docker-compose logs -f frontend" -ForegroundColor Gray
Write-Host "   Detener servicios:  docker-compose down" -ForegroundColor Gray
Write-Host "   Reiniciar:          docker-compose restart" -ForegroundColor Gray
Write-Host ""

# Mostrar logs si se solicita
if ($Logs) {
    Write-Host "Mostrando logs en vivo (Ctrl+C para salir)..." -ForegroundColor Yellow
    Write-Host ""
    docker-compose logs -f
}
