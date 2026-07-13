# ============================================
# GUÍA DE DESPLIEGUE DOCKER - HEALTH AI
# ============================================

## 🚀 Despliegue Rápido

### Opción 1: Usando el script automatizado (RECOMENDADO)

```powershell
# Despliegue normal
.\deploy_docker.ps1

# Reconstruir desde cero (si hay cambios en código)
.\deploy_docker.ps1 -Rebuild

# Limpiar todo y reconstruir
.\deploy_docker.ps1 -Clean -Rebuild

# Ver logs después del despliegue
.\deploy_docker.ps1 -Logs
```

### Opción 2: Comandos manuales

```powershell
# 1. Detener servicios existentes
docker-compose down

# 2. Construir imágenes
docker-compose build

# 3. Iniciar servicios
docker-compose up -d

# 4. Ver logs
docker-compose logs -f
```

## 🔄 Reconstruir después de cambios en el código

### Si modificaste archivos de frontend (frontend_enhanced.py, frontend_styles.py, etc.)

```powershell
# Reconstruir solo el frontend
docker-compose build frontend
docker-compose up -d frontend

# O usar el script
.\deploy_docker.ps1 -Rebuild
```

### Si modificaste archivos de backend (backend.py)

```powershell
# Reconstruir solo el backend
docker-compose build backend
docker-compose up -d backend
```

### Si modificaste requirements.txt

```powershell
# Reconstruir todo sin cache
docker-compose build --no-cache
docker-compose up -d

# O usar el script
.\deploy_docker.ps1 -Clean -Rebuild
```

## 📋 Comandos Útiles

### Ver estado de los contenedores
```powershell
docker-compose ps
```

### Ver logs en tiempo real
```powershell
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend
```

### Reiniciar servicios
```powershell
# Reiniciar todos
docker-compose restart

# Reiniciar solo uno
docker-compose restart backend
docker-compose restart frontend
```

### Detener servicios
```powershell
# Detener sin eliminar
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar contenedores y volúmenes
docker-compose down -v
```

### Acceder a un contenedor
```powershell
# Backend
docker exec -it health-ai-backend bash

# Frontend
docker exec -it health-ai-frontend bash
```

### Ver uso de recursos
```powershell
docker stats
```

## 🔍 Verificar que todo funciona

### 1. Verificar que los contenedores están corriendo
```powershell
docker-compose ps
```

Deberías ver:
```
NAME                   STATUS    PORTS
health-ai-backend      Up        0.0.0.0:8000->8000/tcp
health-ai-frontend     Up        0.0.0.0:8501->8501/tcp
```

### 2. Probar el backend
```powershell
curl http://localhost:8000/health
```

O abre en el navegador: http://localhost:8000/docs

### 3. Probar el frontend
Abre en el navegador: http://localhost:8501

## 🐛 Solución de Problemas

### El contenedor no inicia
```powershell
# Ver logs completos
docker-compose logs backend
docker-compose logs frontend

# Ver últimas 100 líneas
docker-compose logs --tail=100 backend
```

### Puerto ya en uso
```powershell
# En Windows, encontrar qué proceso usa el puerto
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# Detener el proceso (reemplaza PID con el número que aparece)
taskkill /PID <PID> /F
```

### Limpiar todo y empezar de nuevo
```powershell
# Detener todo
docker-compose down -v

# Limpiar imágenes huérfanas
docker system prune -f

# Reconstruir desde cero
.\deploy_docker.ps1 -Clean -Rebuild
```

### Error de conexión a base de datos
```powershell
# Verificar que las variables de entorno son correctas
docker-compose config

# Ver logs del backend para errores de conexión
docker-compose logs backend | Select-String "ERROR"
```

### Actualizar solo el código sin reconstruir
Si solo cambiaste archivos .py y están montados como volúmenes:

```powershell
# Para backend (con --reload activado)
# Los cambios se aplican automáticamente

# Para frontend
docker-compose restart frontend
```

## 📦 Estructura de Archivos Docker

```
.
├── docker-compose.yml          # Configuración de servicios
├── Dockerfile.backend          # Imagen del backend
├── Dockerfile.frontend         # Imagen del frontend
├── deploy_docker.ps1           # Script de despliegue
├── requirements.txt            # Dependencias Python
├── backend.py                  # Código backend
├── frontend_enhanced.py        # Código frontend (principal)
├── frontend_styles.py          # Estilos CSS
├── export_reports.py           # Exportación de reportes
├── ui_components.py            # Componentes UI
└── plotly_themes.py           # Temas de gráficos
```

## 🔐 Variables de Entorno

Las variables están en `docker-compose.yml`:

- `DB_HOST`: Host de Supabase
- `DB_PORT`: Puerto (5432)
- `DB_NAME`: Nombre de BD (postgres)
- `DB_USER`: Usuario de BD
- `DB_PASSWORD`: Contraseña de BD
- `JWT_SECRET`: Secret para JWT
- `N8N_WEBHOOK_URL`: URL del webhook n8n

Para cambiarlas, edita `docker-compose.yml` y reconstruye:

```powershell
docker-compose down
docker-compose up -d
```

## 🌐 URLs de Acceso

- **Frontend (Streamlit)**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## 📊 Monitoreo

### Ver logs en tiempo real con colores
```powershell
docker-compose logs -f --tail=50
```

### Ver uso de CPU y memoria
```powershell
docker stats health-ai-backend health-ai-frontend
```

### Health check del backend
```powershell
curl http://localhost:8000/health
```

## 🎯 Flujo de Desarrollo

1. **Hacer cambios en el código**
2. **Si modificaste archivos Python**:
   ```powershell
   .\deploy_docker.ps1 -Rebuild
   ```
3. **Si modificaste docker-compose.yml o Dockerfiles**:
   ```powershell
   .\deploy_docker.ps1 -Clean -Rebuild
   ```
4. **Ver que todo funciona**:
   ```powershell
   docker-compose logs -f
   ```

## 💡 Tips

- Usa `deploy_docker.ps1` para despliegues automáticos
- Agrega `-Logs` al final para ver logs inmediatamente
- Los cambios en archivos Python montados como volúmenes se reflejan automáticamente en backend (tiene --reload)
- El frontend necesita reinicio: `docker-compose restart frontend`
- Usa `docker-compose down` antes de apagar la PC para evitar problemas

## 🆘 Soporte

Si algo no funciona:
1. Ver logs: `docker-compose logs -f`
2. Verificar estado: `docker-compose ps`
3. Reiniciar: `docker-compose restart`
4. Último recurso: `.\deploy_docker.ps1 -Clean -Rebuild`
