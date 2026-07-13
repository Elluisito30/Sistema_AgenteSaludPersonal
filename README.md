# 🏥 Health AI - Personal Health Assistant

Sistema completo de asistente personal de salud con IA, construido con FastAPI, Streamlit y n8n.

## 📋 Requisitos Previos

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM mínimo
- Conexión a internet (para Supabase)

## 🚀 Instalación Rápida

### 1. Clonar/Descargar el proyecto

```bash
# Si tienes git
git clone <tu-repositorio>
cd health-ai

# O simplemente descarga todos los archivos en una carpeta
```

### 2. Configurar variables de entorno

El archivo `.env` ya está incluido con la configuración de Supabase. Si necesitas cambiar algo:

```bash
nano .env
```

### 3. Dar permisos de ejecución al script de deploy

```bash
chmod +x deploy.sh
```

### 4. Ejecutar el script de instalación

```bash
./deploy.sh
```

Este script:
- ✅ Verifica que Docker esté instalado
- ✅ Construye las imágenes Docker
- ✅ Inicia todos los servicios
- ✅ Muestra las URLs de acceso

## 🌐 Acceso a los Servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:8501 | Interfaz de usuario Streamlit |
| **Backend API** | http://localhost:8000 | API FastAPI |
| **API Docs** | http://localhost:8000/docs | Documentación Swagger |
| **n8n** | http://localhost:5678 | Automatización y workflows |

### Credenciales n8n

```
Usuario: admin
Contraseña: admin123
```

## 📦 Estructura del Proyecto

```
health-ai/
├── backend.py                      # API FastAPI
├── frontend.py                     # Interfaz Streamlit
├── requirements.txt                # Dependencias Python
├── .env                            # Variables de entorno
├── BD.txt                          # Schema de base de datos
├── Personal_Health_Assistant_AI.json # Workflow n8n
├── Dockerfile.backend              # Docker para backend
├── Dockerfile.frontend             # Docker para frontend
├── docker-compose.yml              # Orquestación de servicios
├── .dockerignore                   # Archivos a ignorar
├── deploy.sh                       # Script de instalación
└── README.md                       # Este archivo
```

## 🔧 Comandos Útiles

### Iniciar servicios
```bash
docker-compose up -d
```

### Detener servicios
```bash
docker-compose down
```

### Ver logs en tiempo real
```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend

# Solo n8n
docker-compose logs -f n8n
```

### Reiniciar servicios
```bash
# Todos
docker-compose restart

# Solo uno
docker-compose restart backend
```

### Ver estado de servicios
```bash
docker-compose ps
```

### Reconstruir imágenes (después de cambios en código)
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Entrar a un contenedor
```bash
# Backend
docker exec -it health-ai-backend bash

# Frontend
docker exec -it health-ai-frontend bash

# n8n
docker exec -it health-ai-n8n sh
```

### Limpiar todo (incluyendo volúmenes)
```bash
docker-compose down -v
```

## ⚙️ Configuración de n8n

### 1. Primer acceso

1. Abre http://localhost:5678
2. Login con:
   - Usuario: `admin`
   - Contraseña: `admin123`

### 2. Importar workflow

1. Ve a **Workflows** → **Import from File**
2. Selecciona `Personal_Health_Assistant_AI.json`
3. Haz clic en **Import**

### 3. Configurar credenciales de Supabase

1. Abre el workflow importado
2. Haz clic en el nodo **"💾 Supabase Storage"**
3. Configura las credenciales:
   - **Host**: `db.cfshadkckdlbtpqqfegk.supabase.co`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: `6cEr3VMzIOPpoLdH`
   - **SSL**: `require`

### 4. Activar workflow

1. En el workflow, haz clic en el toggle **"Active"**
2. Verifica que esté en verde

### 5. Probar webhook

```bash
curl -X POST http://localhost:5678/webhook/health-assistant \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "age": 30,
    "weight": 75,
    "height": 175,
    "gender": "male",
    "activity_level": "moderate",
    "sleep_hours": 7,
    "smokes": false,
    "has_chronic_conditions": false,
    "health_goals": ["weight_loss"]
  }'
```

## 🗄️ Base de Datos

El proyecto usa **Supabase** (PostgreSQL) con las siguientes tablas:

- `users` - Usuarios del sistema
- `health_profiles` - Perfiles de salud
- `health_analyses` - Análisis realizados
- `daily_progress` - Progreso diario
- `ml_predictions` - Predicciones ML
- `alerts` - Alertas de salud
- `notifications` - Notificaciones enviadas

### Ejecutar schema manualmente

Si necesitas recrear las tablas:

```bash
# Conectarse a Supabase y ejecutar BD.txt
psql postgresql://postgres:6cEr3VMzIOPpoLdH@db.cfshadkckdlbtpqqfegk.supabase.co:5432/postgres < BD.txt
```

## 📱 Uso del Sistema

### 1. Registrarse

1. Abre http://localhost:8501
2. Ve a la pestaña **"🎯 Registrarse"**
3. Completa el formulario
4. Haz clic en **"Registrarse"**

### 2. Completar perfil

1. En el sidebar, completa tu perfil de salud:
   - Edad, peso, altura
   - Nivel de actividad
   - Horas de sueño
   - Objetivos de salud

2. Haz clic en **"💾 Guardar Perfil"**

### 3. Analizar salud

1. Haz clic en **"🔬 Analizar mi Salud"**
2. Espera 10-30 segundos
3. Verás tu análisis completo con:
   - Health Score
   - BMI y métricas
   - Alertas y recomendaciones
   - Plan de nutrición
   - Plan de ejercicio

### 4. Ver progreso

1. Ve a la pestaña **"📈 Progreso"**
2. Haz clic en **"📊 Ver Historial"** en el sidebar
3. Visualiza tu evolución

## 🐛 Solución de Problemas

### Error: "Cannot connect to database"

```bash
# Verificar que Supabase esté accesible
curl https://db.cfshadkckdlbtpqqfegk.supabase.co

# Verificar logs del backend
docker-compose logs backend
```

### Error: "n8n webhook not responding"

```bash
# Verificar que n8n esté corriendo
docker-compose ps n8n

# Verificar que el workflow esté activo
# Ir a http://localhost:5678 y verificar el toggle "Active"

# Ver logs de n8n
docker-compose logs n8n
```

### Error: "Port already in use"

```bash
# Cambiar puertos en docker-compose.yml
# Por ejemplo:
# - "8001:8000"  # En lugar de 8000:8000
# - "8502:8501"  # En lugar de 8501:8501
```

### Resetear todo

```bash
# Detener y eliminar todo
docker-compose down -v

# Reconstruir desde cero
./deploy.sh
```

## 🔒 Seguridad en Producción

⚠️ **IMPORTANTE**: Este setup es para desarrollo. Para producción:

1. **Cambiar secretos en `.env`**:
   ```bash
   JWT_SECRET=<generar-nuevo-secreto>
   DB_PASSWORD=<cambiar-password>
   ```

2. **Configurar HTTPS** con reverse proxy (nginx, Caddy)

3. **Cambiar credenciales de n8n**:
   ```yaml
   # En docker-compose.yml
   N8N_BASIC_AUTH_USER=tu-usuario
   N8N_BASIC_AUTH_PASSWORD=tu-password-fuerte
   ```

4. **Habilitar firewall** y restringir puertos

5. **Usar variables de entorno** en lugar de hardcodear credenciales

## 📊 Monitoreo

### Ver uso de recursos

```bash
docker stats
```

### Healthchecks

```bash
# Backend
curl http://localhost:8000/health

# n8n
curl http://localhost:5678/healthz
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 🆘 Soporte

- **Issues**: [GitHub Issues]
- **Email**: support@healthai.com
- **Discord**: [Community Server]

## 🎯 Roadmap

- [ ] Integración con Apple Health / Google Fit
- [ ] App móvil (React Native)
- [ ] Modelo ML personalizado (TensorFlow)
- [ ] Chatbot con GPT-4
- [ ] Integración con wearables
- [ ] Multi-idioma
- [ ] Dark mode

---

**Hecho con ❤️ por el equipo de Health AI**