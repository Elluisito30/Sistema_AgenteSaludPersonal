#!/bin/bash

# ============================================
# HEALTH AI - DOCKER DEPLOYMENT SCRIPT
# ============================================

set -e

echo "=========================================="
echo "🏥 Health AI - Docker Deployment"
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Por favor, instala Docker primero."
    exit 1
fi

print_message "Docker encontrado"

# Verificar que Docker Compose está instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose no está instalado. Por favor, instala Docker Compose primero."
    exit 1
fi

print_message "Docker Compose encontrado"

# Verificar que los archivos necesarios existen
required_files=("backend.py" "frontend.py" "requirements.txt" ".env" "Dockerfile.backend" "Dockerfile.frontend" "docker-compose.yml")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Archivo $file no encontrado"
        exit 1
    fi
done

print_message "Todos los archivos necesarios están presentes"

# Detener contenedores existentes
echo ""
echo "🛑 Deteniendo contenedores existentes..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

# Construir imágenes
echo ""
echo "🔨 Construyendo imágenes Docker..."
if docker compose version &> /dev/null; then
    docker compose build --no-cache
else
    docker-compose build --no-cache
fi

print_message "Imágenes construidas exitosamente"

# Iniciar servicios
echo ""
echo "🚀 Iniciando servicios..."
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

# Esperar a que los servicios estén listos
echo ""
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado de los servicios
echo ""
echo "📊 Estado de los servicios:"
if docker compose version &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

# Mostrar información de acceso
echo ""
echo "=========================================="
echo "✅ Servicios iniciados correctamente"
echo "=========================================="
echo ""
echo "📍 URLs de acceso:"
echo "  • Frontend (Streamlit): http://localhost:8501"
echo "  • Backend (FastAPI):    http://localhost:8000"
echo "  • API Docs (Swagger):   http://localhost:8000/docs"
echo "  • n8n Automation:       http://localhost:5678"
echo ""
echo "🔐 Credenciales n8n:"
echo "  • Usuario: admin"
echo "  • Contraseña: admin123"
echo ""
echo "=========================================="
echo ""
echo "📝 Comandos útiles:"
echo "  • Ver logs:           docker-compose logs -f"
echo "  • Detener servicios:  docker-compose down"
echo "  • Reiniciar:          docker-compose restart"
echo "  • Ver estado:         docker-compose ps"
echo ""
echo "🔧 Para configurar n8n:"
echo "  1. Accede a http://localhost:5678"
echo "  2. Importa el workflow desde Personal_Health_Assistant_AI.json"
echo "  3. Activa el workflow"
echo ""
echo "=========================================="