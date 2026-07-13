#!/bin/bash

# ============================================
# HEALTH AI - MANAGEMENT SCRIPT
# ============================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

show_menu() {
    clear
    print_header "🏥 Health AI - Management Menu"
    echo ""
    echo "1)  🚀 Iniciar servicios"
    echo "2)  🛑 Detener servicios"
    echo "3)  🔄 Reiniciar servicios"
    echo "4)  📊 Ver estado"
    echo "5)  📝 Ver logs (todos)"
    echo "6)  📝 Ver logs (backend)"
    echo "7)  📝 Ver logs (frontend)"
    echo "8)  📝 Ver logs (n8n)"
    echo "9)  🔨 Reconstruir imágenes"
    echo "10) 🧹 Limpiar todo"
    echo "11) 🏥 Health check"
    echo "12) 💻 Shell (backend)"
    echo "13) 💻 Shell (frontend)"
    echo "14) 💻 Shell (n8n)"
    echo "15) 📈 Ver recursos (stats)"
    echo "16) 🔍 Inspeccionar red"
    echo "0)  🚪 Salir"
    echo ""
    echo -n "Selecciona una opción: "
}

start_services() {
    print_header "🚀 Iniciando servicios..."
    if docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null; then
        print_success "Servicios iniciados"
        echo ""
        print_info "URLs de acceso:"
        echo "  • Frontend: http://localhost:8501"
        echo "  • Backend:  http://localhost:8000"
        echo "  • n8n:      http://localhost:5678"
    else
        print_error "Error al iniciar servicios"
    fi
}

stop_services() {
    print_header "🛑 Deteniendo servicios..."
    if docker compose down 2>/dev/null || docker-compose down 2>/dev/null; then
        print_success "Servicios detenidos"
    else
        print_error "Error al detener servicios"
    fi
}

restart_services() {
    print_header "🔄 Reiniciando servicios..."
    if docker compose restart 2>/dev/null || docker-compose restart 2>/dev/null; then
        print_success "Servicios reiniciados"
    else
        print_error "Error al reiniciar servicios"
    fi
}

view_status() {
    print_header "📊 Estado de los servicios"
    docker compose ps 2>/dev/null || docker-compose ps 2>/dev/null
}

view_all_logs() {
    print_header "📝 Logs de todos los servicios (Ctrl+C para salir)"
    docker compose logs -f 2>/dev/null || docker-compose logs -f 2>/dev/null
}

view_backend_logs() {
    print_header "📝 Logs del Backend (Ctrl+C para salir)"
    docker compose logs -f backend 2>/dev/null || docker-compose logs -f backend 2>/dev/null
}

view_frontend_logs() {
    print_header "📝 Logs del Frontend (Ctrl+C para salir)"
    docker compose logs -f frontend 2>/dev/null || docker-compose logs -f frontend 2>/dev/null
}

view_n8n_logs() {
    print_header "📝 Logs de n8n (Ctrl+C para salir)"
    docker compose logs -f n8n 2>/dev/null || docker-compose logs -f n8n 2>/dev/null
}

rebuild_images() {
    print_header "🔨 Reconstruyendo imágenes..."
    if docker compose build --no-cache 2>/dev/null || docker-compose build --no-cache 2>/dev/null; then
        print_success "Imágenes reconstruidas"
        echo ""
        print_info "Reiniciando servicios..."
        docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null
        print_success "Servicios actualizados"
    else
        print_error "Error al reconstruir imágenes"
    fi
}

clean_all() {
    print_header "🧹 Limpiando todo..."
    echo -n "⚠️  Esto eliminará todos los contenedores, imágenes y volúmenes. ¿Continuar? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker compose down -v 2>/dev/null || docker-compose down -v 2>/dev/null
        docker system prune -f
        print_success "Sistema limpiado"
    else
        print_info "Operación cancelada"
    fi
}

health_check() {
    print_header "🏥 Health Check"
    
    echo "Backend:"
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend: OK"
    else
        print_error "Backend: No responde"
    fi
    
    echo ""
    echo "Frontend:"
    if curl -s http://localhost:8501 > /dev/null; then
        print_success "Frontend: OK"
    else
        print_error "Frontend: No responde"
    fi
    
    echo ""
    echo "n8n:"
    if curl -s http://localhost:5678/healthz > /dev/null; then
        print_success "n8n: OK"
    else
        print_error "n8n: No responde"
    fi
}

shell_backend() {
    print_header "💻 Shell - Backend"
    docker exec -it health-ai-backend bash
}

shell_frontend() {
    print_header "💻 Shell - Frontend"
    docker exec -it health-ai-frontend bash
}

shell_n8n() {
    print_header "💻 Shell - n8n"
    docker exec -it health-ai-n8n sh
}

view_stats() {
    print_header "📈 Recursos del sistema (Ctrl+C para salir)"
    docker stats
}

inspect_network() {
    print_header "🔍 Inspección de red"
    docker network inspect health-ai-network
}

# Main loop
while true; do
    show_menu
    read -r option
    
    case $option in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) view_status ;;
        5) view_all_logs ;;
        6) view_backend_logs ;;
        7) view_frontend_logs ;;
        8) view_n8n_logs ;;
        9) rebuild_images ;;
        10) clean_all ;;
        11) health_check ;;
        12) shell_backend ;;
        13) shell_frontend ;;
        14) shell_n8n ;;
        15) view_stats ;;
        16) inspect_network ;;
        0) 
            print_header "👋 ¡Hasta luego!"
            exit 0
            ;;
        *)
            print_error "Opción inválida"
            ;;
    esac
    
    echo ""
    echo -n "Presiona Enter para continuar..."
    read -r
done