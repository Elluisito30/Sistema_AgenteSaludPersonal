# main.py - FastAPI Backend con PostgreSQL directo

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from dotenv import load_dotenv
load_dotenv()  # ← Load .env file
import socket
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import jwt
import bcrypt
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import json
from decimal import Decimal
from datetime import datetime, timedelta, timezone
# ============================================
# CONFIGURACIÓN
# ============================================

app = FastAPI(
    title="Health AI API",
    description="Sistema de Salud Personal con IA",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Config
SECRET_KEY = os.getenv("JWT_SECRET", "68439d1d5eff6f5abf09e85b7f1cf5bbed73bd7ac3d513d3")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Security
security = HTTPBearer()

# N8N Webhook URL
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook-test/health-assistant-DOCKER")
N8N_WEBHOOK_TEST_URL = os.getenv("N8N_WEBHOOK_TEST_URL", "http://n8n:5678/webhook-test/health-assistant-DOCKER")

# ============================================
# POSTGRESQL CONNECTION - FORZAR IPv4
# ============================================

import socket

def resolve_hostname_to_ipv4(hostname):
    """Resolver hostname a dirección IPv4"""
    try:
        # Forzar resolución a IPv4
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        ipv4_address = addr_info[0][4][0]
        print(f"✅ {hostname} resuelto a IPv4: {ipv4_address}")
        return ipv4_address
    except socket.gaierror as e:
        print(f"❌ Error resolviendo {hostname}: {e}")
        return hostname

# PostgreSQL Connection Pool - Supabase Session Pooler
DB_HOST_ORIGINAL = os.getenv("DB_HOST", "aws-1-us-east-2.pooler.supabase.com")
# Use the original hostname (required for TLS SNI with Supabase session pooler)
DB_HOST = DB_HOST_ORIGINAL
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "6cEr3VMzIOPpoLdH")

# URL de conexión
# Usar SSL solo si no es base de datos local
ssl_mode = "require" if DB_HOST not in ("db", "localhost", "127.0.0.1") else "disable"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={ssl_mode}"

print(f"🔗 Conectando a: {DB_HOST}:{DB_PORT} con usuario: {DB_USER}")
# Connection pool - inicialización lazy (no conecta al inicio)
db_pool = None

def get_db_pool():
    """Inicializar pool de conexiones solo cuando se necesite"""
    global db_pool
    if db_pool is None:
        try:
            db_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            print("✅ Conexión a base de datos establecida")
        except Exception as e:
            print(f"❌ Error conectando a BD: {str(e)}")
            raise
    return db_pool

@contextmanager
def get_db_connection():
    """Context manager para obtener conexión del pool"""
    pool = get_db_pool()  # ← Usa la función lazy
    conn = pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=True):
    """Context manager para obtener cursor con auto-commit"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

# ============================================
# MODELOS PYDANTIC
# ============================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class HealthProfile(BaseModel):
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    sleep_hours: int
    smokes: bool = False
    has_chronic_conditions: bool = False
    chronic_conditions_detail: Optional[str] = None
    genetics_risk: Optional[str] = 'low'
    health_goals: List[str] = []
    chronic_diseases: List[str] = []
    genetic_risk_factors: List[str] = []

class DailyProgress(BaseModel):
    date: str
    weight_kg: Optional[float] = None
    steps_count: Optional[int] = None
    exercise_minutes: Optional[int] = None
    calories_consumed: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fats_g: Optional[float] = None
    water_liters: Optional[float] = None
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    mood: Optional[int] = None
    energy_level: Optional[int] = None
    notes: Optional[str] = None

# ============================================
# UTILIDADES
# ============================================

def convert_to_json_serializable(obj):
    """Convierte recursivamente objetos Decimal y datetime a tipos JSON-serializables"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, )):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(i) for i in obj]
    return obj

# ============================================
# UTILIDADES JWT
# ============================================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================

@app.post("/api/register")
def register(user: UserRegister):
    """Registrar nuevo usuario"""
    
    with get_db_cursor() as cursor:
        # Verificar si email existe
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email ya registrado")
        
        # Hash password
        password_hash = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, phone_number)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (user.email, password_hash, user.full_name, user.phone_number))
        
        user_id = cursor.fetchone()['id']
    
    # Crear token
    token = create_access_token({"user_id": user_id})
    
    return {
        "message": "Usuario registrado exitosamente",
        "user_id": user_id,
        "access_token": token,
        "token_type": "bearer"
    }

@app.post("/api/login")
def login(credentials: UserLogin):
    """Login de usuario"""
    
    with get_db_cursor() as cursor:
        # Buscar usuario
        cursor.execute("""
            SELECT id, password_hash, full_name, email
            FROM users
            WHERE email = %s AND is_active = TRUE
        """, (credentials.email,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Verificar password
        if not bcrypt.checkpw(credentials.password.encode(), user['password_hash'].encode()):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Actualizar last_login
        cursor.execute("""
            UPDATE users SET last_login = NOW()
            WHERE id = %s
        """, (user['id'],))
    
    # Crear token
    token = create_access_token({"user_id": user['id']})
    
    return {
        "message": "Login exitoso",
        "user_id": user['id'],
        "full_name": user['full_name'],
        "email": user['email'],
        "access_token": token,
        "token_type": "bearer"
    }

# ============================================
# ENDPOINTS DE PERFIL
# ============================================

@app.post("/api/profile")
def create_profile(profile: HealthProfile, user_id: int = Depends(verify_token)):
    """Crear o actualizar perfil de salud"""
    
    with get_db_cursor() as cursor:
        # Verificar si existe perfil
        cursor.execute("SELECT id FROM health_profiles WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar
            cursor.execute("""
                UPDATE health_profiles SET
                    age = %s, gender = %s, height_cm = %s, weight_kg = %s,
                    activity_level = %s, sleep_hours = %s, smokes = %s,
                    has_chronic_conditions = %s, chronic_conditions_detail = %s,
                    genetics_risk = %s, health_goals = %s, 
                    chronic_diseases = %s, genetic_risk_factors = %s, updated_at = NOW()
                WHERE user_id = %s
            """, (profile.age, profile.gender, profile.height_cm, profile.weight_kg,
                  profile.activity_level, profile.sleep_hours, profile.smokes,
                  profile.has_chronic_conditions, profile.chronic_conditions_detail,
                  profile.genetics_risk, profile.health_goals, 
                  profile.chronic_diseases, profile.genetic_risk_factors, user_id))
        else:
            # Insertar
            cursor.execute("""
                INSERT INTO health_profiles 
                (user_id, age, gender, height_cm, weight_kg, activity_level, 
                 sleep_hours, smokes, has_chronic_conditions, chronic_conditions_detail, 
                 genetics_risk, health_goals, chronic_diseases, genetic_risk_factors)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, profile.age, profile.gender, profile.height_cm, profile.weight_kg,
                  profile.activity_level, profile.sleep_hours, profile.smokes,
                  profile.has_chronic_conditions, profile.chronic_conditions_detail,
                  profile.genetics_risk, profile.health_goals,
                  profile.chronic_diseases, profile.genetic_risk_factors))
    
    return {"message": "Perfil actualizado exitosamente"}

@app.get("/api/profile")
def get_profile(user_id: int = Depends(verify_token)):
    """Obtener perfil de salud"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        return dict(profile)

# ============================================
# ENDPOINT DE ANÁLISIS CON N8N
# ============================================

@app.post("/analyze-health")
def analyze_health_from_n8n(data: dict):
    """Endpoint para que n8n llame (si es necesario)"""
    # Este es el endpoint que n8n está intentando llamar
    # Retorna análisis simple sin IA
    return {
        "health_risk": "medium",
        "fitness_level": "intermediate",
        "predicted_improvements": {},
        "nutrient_recommendations": {},
        "confidence_score": 0.85
    }

@app.post("/api/analyze")
def analyze_health(user_id: int = Depends(verify_token)):
    """Realizar análisis completo de salud (local, sin n8n)"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil no encontrado. Crea tu perfil primero.")
        
        profile = convert_to_json_serializable(dict(profile))
    
    # Calcular métricas localmente
    age = profile.get('age', 30)
    weight = profile.get('weight_kg', 70)
    height = profile.get('height_cm', 170)
    gender = profile.get('gender', 'male')
    activity = profile.get('activity_level', 'moderate')
    sleep = profile.get('sleep_hours', 7)
    smokes = profile.get('smokes', False)
    has_chronic = profile.get('has_chronic_conditions', False)
    genetics_risk = profile.get('genetics_risk', 'low')
    goals = profile.get('health_goals', [])
    chronic_diseases = profile.get('chronic_diseases', [])
    if chronic_diseases is None: chronic_diseases = []
    genetic_risk_factors = profile.get('genetic_risk_factors', [])
    if genetic_risk_factors is None: genetic_risk_factors = []

    # BMI y Categorías
    bmi = round(weight / ((height / 100) ** 2), 1)
    if bmi < 16:
        bmi_category = "severely_underweight"
    elif bmi < 18.5:
        bmi_category = "underweight"
    elif bmi < 25:
        bmi_category = "normal"
    elif bmi < 30:
        bmi_category = "overweight"
    elif bmi < 35:
        bmi_category = "obese_1"
    else:
        bmi_category = "obese_2_3"

    # BMR (Mifflin-St Jeor)
    if gender == "male":
        bmr = round(10 * weight + 6.25 * height - 5 * age + 5, 2)
    else:
        bmr = round(10 * weight + 6.25 * height - 5 * age - 161, 2)

    # TDEE
    activity_multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9
    }
    tdee = round(bmr * activity_multipliers.get(activity, 1.55), 2)

    # ==========================================
    # LÓGICA DE HEALTH SCORE REFACTORIZADA
    # ==========================================
    score = 100
    has_penalties = False
    
    # 1. Puntuación Base por IMC
    if 25 <= bmi < 30:
        score -= 15
        has_penalties = True
    elif 30 <= bmi < 35:
        score -= 25
        has_penalties = True
    elif bmi >= 35:
        score -= 40
        has_penalties = True
    elif 16 <= bmi < 18.5:
        score -= 20
        has_penalties = True
    elif bmi < 16:
        score -= 35
        has_penalties = True
        
    # 2. Penalizaciones Acumulativas
    if smokes:
        score -= 20
        has_penalties = True
        
    has_diabetes = False
    for disease in chronic_diseases:
        d = disease.lower()
        if "diabetes" in d:
            score -= 25
            has_diabetes = True
            has_penalties = True
        elif "hipertensión" in d or "hipertension" in d:
            score -= 15
            has_penalties = True
        elif "colesterol" in d:
            score -= 10
            has_penalties = True

    if len(genetic_risk_factors) > 0:
        score -= 10
        has_penalties = True

    if sleep < 6:
        score -= 8
        has_penalties = True
    elif sleep > 9:
        score -= 3
        has_penalties = True

    if activity in ["sedentary", "none", "sedentario"]:
        score -= 10
        has_penalties = True

    # 3. Limitadores de Puntaje Máximo
    if bmi < 16 or bmi >= 35:
        if score > 40:
            score = 40
            
    if has_diabetes and smokes:
        if score > 45:
            score = 45

    score = max(0, min(100, score))
    
    # 4. Clasificación Final
    if score <= 20:
        health_risk = "Crítico - Requiere atención médica URGENTE"
    elif score <= 40:
        health_risk = "Alto Riesgo - Consulta a tu médico de cabecera"
    elif score <= 60:
        health_risk = "Riesgo Moderado - Mejora tus hábitos"
    elif score <= 80:
        health_risk = "Aceptable - Mantén tus hábitos saludables"
    else:
        if has_penalties:
            health_risk = "Aceptable - Mantén tus hábitos saludables"
        else:
            health_risk = "Buen estado - Sigue así"

    if score >= 60:
        fitness_level = "intermediate"
    else:
        fitness_level = "beginner"
        
    # 5. Lógica adaptativa de Objetivos
    def validate_user_goals(current_goals, current_bmi):
        adjusted = list(current_goals)
        alerts_goal = []
        if current_bmi < 18.5:
            if "weight_loss" in adjusted:
                adjusted.remove("weight_loss")
                alerts_goal.append({"priority": "high", "message": "Tu objetivo de pérdida de peso fue bloqueado debido a tu bajo peso."})
            if "muscle_gain" not in adjusted:
                adjusted.append("muscle_gain")
        elif current_bmi > 30:
            if "muscle_gain" in adjusted:
                adjusted.remove("muscle_gain")
                alerts_goal.append({"priority": "medium", "message": "Priorizamos la pérdida de peso sobre ganancia muscular debido a tu IMC."})
            if "weight_loss" not in adjusted:
                adjusted.append("weight_loss")
        return adjusted, alerts_goal

    goals, goal_alerts = validate_user_goals(goals, bmi)

    # Alerts
    alerts = []
    alerts.extend(goal_alerts)
    if bmi >= 30:
        alerts.append({"priority": "high", "message": "Tu BMI indica obesidad. Consulta a un especialista."})
    elif bmi >= 25:
        alerts.append({"priority": "medium", "message": "Tu BMI indica sobrepeso. Considera ajustar tu dieta."})
    if smokes:
        alerts.append({"priority": "high", "message": "Fumar aumenta significativamente tu riesgo de salud."})
        
    # Nuevas recomendaciones por enfermedades
    for disease in chronic_diseases:
        disease_lower = disease.lower()
        if "diabetes" in disease_lower:
            alerts.append({"priority": "high", "message": "🚨 Alerta Clínica: Plan de comidas bajo en carbohidratos recomendado debido a la Diabetes."})
        elif "hipertensión" in disease_lower or "hipertension" in disease_lower:
            alerts.append({"priority": "high", "message": "🚨 Alerta Clínica: Evita el exceso de sodio y mantén chequeos de presión arterial por tu Hipertensión."})
        elif "colesterol" in disease_lower:
            alerts.append({"priority": "high", "message": "🚨 Alerta Clínica: Reduce el consumo de grasas saturadas debido al Colesterol alto."})
        else:
            alerts.append({"priority": "high", "message": f"🚨 Alerta Clínica: Sigue las indicaciones médicas para: {disease}."})
            
    if len(genetic_risk_factors) > 0:
        alerts.append({"priority": "medium", "message": "⚠️ Tienes factores de riesgo genético. Se recomiendan chequeos preventivos regulares."})

    if sleep < 6:
        alerts.append({"priority": "medium", "message": "Duermes menos de 6 horas. Intenta mejorar tu descanso."})
    if activity == "sedentary":
        alerts.append({"priority": "medium", "message": "Tu nivel de actividad es muy bajo. Intenta caminar 30 min al día."})

    # Weekly goals
    weekly_goals = []
    goal_templates = {
        "weight_loss": "Reducir 500 calorías diarias",
        "muscle_gain": "Aumentar consumo de proteína a 1.6g/kg",
        "better_sleep": "Dormir al menos 7-8 horas diarias",
        "stress_reduction": "Practicar 10 min de meditación al día",
        "energy_boost": "Hacer ejercicio 30 min diarios",
        "general_wellness": "Tomar 2 litros de agua al día"
    }
    for g in goals:
        if g in goal_templates:
            weekly_goals.append(goal_templates[g])
    if not weekly_goals:
        weekly_goals = ["Mantener una dieta balanceada", "Ejercicio 3 veces por semana", "Dormir al menos 7 horas"]

    # Nutrition plan adaptativo
    daily_calories_diff = 0
    if bmi < 18.5 and "muscle_gain" in goals:
        daily_calories_diff = 500  # Forzar superávit calórico
    elif "weight_loss" in goals:
        daily_calories_diff = -300

    protein_ratio = 0.3 if "muscle_gain" in goals else 0.25
    carbs_ratio = 0.4 if "weight_loss" not in goals else 0.35
    fats_ratio = 0.3 if "weight_loss" not in goals else 0.4
    
    # Exercise plan based on activity level and goals
    exercise_plans = {
        "sedentary": {"cardio": "20 min, 3 días/semana", "strength": "15 min, 2 días/semana", "flexibility": "10 min/día"},
        "light": {"cardio": "30 min, 3 días/semana", "strength": "20 min, 2 días/semana", "flexibility": "10 min/día"},
        "moderate": {"cardio": "40 min, 4 días/semana", "strength": "25 min, 3 días/semana", "flexibility": "10 min/día"},
        "active": {"cardio": "50 min, 5 días/semana", "strength": "30 min, 3 días/semana", "flexibility": "15 min/día"},
        "very_active": {"cardio": "60 min, 6 días/semana", "strength": "35 min, 4 días/semana", "flexibility": "15 min/día"}
    }
    
    health_plan = {
        "nutrition": {
            "daily_calories": int(tdee + daily_calories_diff),
            "macronutrients": {
                "protein": int(tdee * protein_ratio / 4),
                "carbs": int(tdee * carbs_ratio / 4),
                "fats": int(tdee * fats_ratio / 9)
            },
            "recommendations": [
                "Prioriza alimentos no procesados" if "weight_loss" in goals else "Mantén una dieta variada",
                "Aumenta consumo de fibra",
                "Distribuye comidas en 4-5 porciones al día"
            ]
        },
        "exercise": exercise_plans.get(activity, exercise_plans["moderate"])
    }

    # Predictions placeholder
    weight_diff = 0
    if "weight_loss" in goals:
        weight_diff = -0.5
    elif "muscle_gain" in goals:
        weight_diff = 0.3
        
    predictions = {
        "predictions_data": {
            "predictions": {
                "2_weeks": {"weight_kg": round(weight + (weight_diff * 2), 1)},
                "1_month": {"weight_kg": round(weight + (weight_diff * 4), 1)},
                "6_months": {"weight_kg": round(weight + (weight_diff * 24), 1)}
            }
        },
        "model_used": "local_calculator_v1",
        "confidence_score": 0.85,
        "is_active": True
    }

    analysis_result = {
        "health_score": score,
        "bmi": bmi,
        "bmi_category": bmi_category,
        "bmr": bmr,
        "tdee": tdee,
        "health_risk": health_risk,
        "fitness_level": fitness_level,
        "health_plan": health_plan,
        "alerts": alerts,
        "weekly_goals": weekly_goals,
        "next_checkup": (datetime.now() + timedelta(days=30)).date().isoformat(),
        "confidence_score": 0.85,
        "predictions": predictions,
        "analyzed_at": datetime.now().isoformat()
    }

    # Guardar análisis en la BD
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO health_analyses
                (user_id, bmi, bmi_category, bmr, tdee, health_score,
                 health_risk, fitness_level, health_plan, alerts,
                 weekly_goals, next_checkup, confidence_score,
                 nutrient_recommendations, predicted_improvements, analyzed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                        %s::jsonb, %s, %s::date, %s, %s::jsonb, %s::jsonb, NOW())
            """, (
                user_id, bmi, bmi_category, bmr, tdee, score,
                health_risk, fitness_level, json.dumps(health_plan),
                json.dumps(alerts), weekly_goals,
                (datetime.now() + timedelta(days=30)).date(),
                0.85, json.dumps({}), json.dumps({})
            ))
            cursor.execute("SELECT LASTVAL()")
            analysis_id = cursor.fetchone()['lastval']

            # Guardar predicción
            profile_snapshot = {
                "weight": weight, "height": height, "age": age,
                "gender": gender, "activity_level": activity
            }
            expires_at = (datetime.now() + timedelta(days=90)).isoformat()
            cursor.execute("""
                INSERT INTO health_predictions
                (user_id, analysis_id, profile_snapshot, predictions_data,
                 model_used, confidence_score, is_active, expires_at)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, TRUE, %s::timestamp)
            """, (
                user_id, analysis_id, json.dumps(profile_snapshot),
                json.dumps(predictions['predictions_data']),
                predictions['model_used'], predictions['confidence_score'],
                expires_at
            ))
    except Exception as e:
        print(f"⚠️ Error guardando análisis en BD: {e}")

    print(f"✅ Análisis local completado - health_score: {score}")
    return analysis_result

# ============================================
# ENDPOINTS DE HISTORIAL
# ============================================

@app.get("/api/history")
def get_history(limit: int = 20, user_id: int = Depends(verify_token)):
    """Obtener historial de análisis"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT id, health_score, bmi, bmi_category, health_risk, 
                   fitness_level, analyzed_at, next_checkup
            FROM health_analyses
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT %s
        """, (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]

@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: int, user_id: int = Depends(verify_token)):
    """Obtener análisis específico"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM health_analyses
            WHERE id = %s AND user_id = %s
        """, (analysis_id, user_id))
        
        analysis = cursor.fetchone()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        
        return dict(analysis)

# ============================================
# ENDPOINTS DE PROGRESO DIARIO
# ============================================

@app.post("/api/progress")
def add_progress(progress: DailyProgress, user_id: int = Depends(verify_token)):
    """Agregar progreso diario"""
    
    with get_db_cursor() as cursor:
        # Verificar si existe registro para esa fecha
        cursor.execute("""
            SELECT id FROM daily_progress
            WHERE user_id = %s AND date = %s
        """, (user_id, progress.date))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar
            cursor.execute("""
                UPDATE daily_progress SET
                    weight_kg = %s, steps_count = %s, exercise_minutes = %s,
                    calories_consumed = %s, protein_g = %s, carbs_g = %s,
                    fats_g = %s, water_liters = %s, sleep_hours = %s,
                    sleep_quality = %s, stress_level = %s, mood = %s,
                    energy_level = %s, notes = %s
                WHERE id = %s
            """, (
                progress.weight_kg, progress.steps_count, progress.exercise_minutes,
                progress.calories_consumed, progress.protein_g, progress.carbs_g,
                progress.fats_g, progress.water_liters, progress.sleep_hours,
                progress.sleep_quality, progress.stress_level, progress.mood,
                progress.energy_level, progress.notes, existing['id']
            ))
        else:
            # Insertar
            cursor.execute("""
                INSERT INTO daily_progress
                (user_id, date, weight_kg, steps_count, exercise_minutes,
                 calories_consumed, protein_g, carbs_g, fats_g, water_liters,
                 sleep_hours, sleep_quality, stress_level, mood, energy_level, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, progress.date, progress.weight_kg, progress.steps_count,
                progress.exercise_minutes, progress.calories_consumed, progress.protein_g,
                progress.carbs_g, progress.fats_g, progress.water_liters,
                progress.sleep_hours, progress.sleep_quality, progress.stress_level,
                progress.mood, progress.energy_level, progress.notes
            ))
    
    return {"message": "Progreso registrado exitosamente"}

@app.get("/api/progress")
def get_progress(days: int = 30, user_id: int = Depends(verify_token)):
    """Obtener progreso de últimos N días"""
    
    with get_db_cursor(commit=False) as cursor:
        date_limit = (datetime.now() - timedelta(days=days)).date()
        
        cursor.execute("""
            SELECT * FROM daily_progress
            WHERE user_id = %s AND date >= %s
            ORDER BY date DESC
        """, (user_id, date_limit))
        
        return [dict(row) for row in cursor.fetchall()]

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
def root():
    return {
        "service": "Health AI API",
        "version": "2.0.0",
        "status": "running",
        "database": "PostgreSQL Direct Connection",
        "n8n_webhook": N8N_WEBHOOK_URL,
        "endpoints": {
            "auth": ["/api/register", "/api/login"],
            "profile": ["/api/profile"],
            "analysis": ["/api/analyze", "/api/history"],
            "progress": ["/api/progress"]
        }
    }

@app.get("/health")
def health_check():
    """Health check con verificación de DB y n8n"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Verificar n8n
    try:
        n8n_response = requests.get(N8N_WEBHOOK_URL.replace('/webhook/', '/healthz'), timeout=2)
        n8n_status = "reachable"
    except:
        n8n_status = "unreachable"
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "n8n": n8n_status,
        "n8n_webhook_url": N8N_WEBHOOK_URL
    }

# ============================================
# SHUTDOWN
# ============================================

@app.on_event("shutdown")
def shutdown():
    """Cerrar pool de conexiones"""
    global db_pool
    if db_pool is not None:
        db_pool.closeall()

# Agregar estos endpoints al backend.py existente (después de los endpoints actuales)

# ============================================
# ENDPOINTS DE PREDICCIONES
# ============================================

@app.get("/api/predictions/latest")
def get_latest_prediction(user_id: int = Depends(verify_token)):
    """Obtener última predicción activa del usuario"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                id,
                user_id,
                analysis_id,
                profile_snapshot,
                predictions_data,
                model_used,
                confidence_score,
                created_at,
                expires_at
            FROM health_predictions
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        prediction = cursor.fetchone()
        
        if not prediction:
            raise HTTPException(
                status_code=404, 
                detail="No hay predicciones activas. Realiza un análisis primero."
            )
        
        result = convert_to_json_serializable(dict(prediction))
        
        # ✅ FIX: Comparar con datetime AWARE
        if result.get('expires_at'):
            expires_str = result['expires_at']
            if isinstance(expires_str, str):
                # Parsear string ISO y hacerlo timezone-aware
                expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)  # ← USAR UTC
                
                if expires < now:
                    result['is_expired'] = True
                    result['message'] = "Esta predicción ha expirado. Genera una nueva."
        
        return result


@app.get("/api/predictions/history")
def get_predictions_history(limit: int = 10, user_id: int = Depends(verify_token)):
    """Obtener historial completo de predicciones"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                id,
                created_at,
                expires_at,
                is_active,
                model_used,
                confidence_score,
                predictions_data->'predictions'->'6_months'->>'weight_kg' AS predicted_weight,
                profile_snapshot->>'weight' AS initial_weight
            FROM health_predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        
        predictions = [convert_to_json_serializable(dict(row)) for row in cursor.fetchall()]
        return {
            "total": len(predictions),
            "predictions": predictions
        }

@app.get("/api/predictions/{prediction_id}")
def get_prediction_detail(prediction_id: int, user_id: int = Depends(verify_token)):
    """Obtener detalle completo de una predicción específica"""
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM health_predictions
            WHERE id = %s AND user_id = %s
        """, (prediction_id, user_id))
        
        prediction = cursor.fetchone()
        
        if not prediction:
            raise HTTPException(status_code=404, detail="Predicción no encontrada")
        
        return convert_to_json_serializable(dict(prediction))

@app.get("/api/predictions/timeline")
def get_predictions_timeline(user_id: int = Depends(verify_token)):
    """
    Comparar predicciones con progreso real
    Retorna: predicción activa + progreso real desde fecha de predicción
    """
    
    with get_db_cursor(commit=False) as cursor:
        # Obtener predicción activa
        cursor.execute("""
            SELECT 
                id,
                created_at,
                predictions_data,
                profile_snapshot
            FROM health_predictions
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        prediction = cursor.fetchone()
        
        if not prediction:
            return {
                "has_predictions": False,
                "message": "No hay predicciones activas para comparar"
            }
        
        prediction_date = prediction['created_at']
        
        # Obtener progreso real desde la fecha de predicción
        cursor.execute("""
            SELECT 
                date,
                weight_kg,
                exercise_minutes,
                sleep_hours,
                mood,
                energy_level,
                steps_count,
                calories_consumed
            FROM daily_progress
            WHERE user_id = %s
            AND date >= %s::date
            ORDER BY date ASC
        """, (user_id, prediction_date))
        
        actual_progress = [convert_to_json_serializable(dict(row)) for row in cursor.fetchall()]
        
        # Calcular adherencia al plan (si hay progreso)
        adherence_score = 0
        if actual_progress:
            # Lógica simple: si registró al menos 50% de los días
            days_since = (datetime.now().date() - prediction_date.date()).days
            days_logged = len(actual_progress)
            adherence_score = min(100, int((days_logged / max(days_since, 1)) * 100))
        
        return {
            "has_predictions": True,
            "prediction_id": prediction['id'],
            "prediction_date": prediction_date.isoformat(),
            "prediction": convert_to_json_serializable(dict(prediction)),
            "actual_progress": actual_progress,
            "adherence_score": adherence_score,
            "days_tracked": len(actual_progress)
        }

@app.post("/api/predictions/deactivate/{prediction_id}")
def deactivate_prediction(prediction_id: int, user_id: int = Depends(verify_token)):
    """Desactivar una predicción manualmente"""
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE health_predictions
            SET is_active = FALSE
            WHERE id = %s AND user_id = %s
            RETURNING id
        """, (prediction_id, user_id))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Predicción no encontrada")
        
        return {
            "message": "Predicción desactivada exitosamente",
            "prediction_id": result['id']
        }

@app.get("/api/predictions/stats")
def get_prediction_stats(user_id: int = Depends(verify_token)):
    """
    Obtener estadísticas de precisión de predicciones pasadas
    Compara predicciones con resultados reales
    """
    
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                hp.id,
                hp.created_at,
                (hp.profile_snapshot->>'weight')::DECIMAL AS initial_weight,
                (hp.predictions_data->'predictions'->'2_weeks'->>'weight_kg')::DECIMAL AS pred_2w,
                (hp.predictions_data->'predictions'->'1_month'->>'weight_kg')::DECIMAL AS pred_1m,
                
                -- Peso real a las 2 semanas
                (
                    SELECT dp.weight_kg
                    FROM daily_progress dp
                    WHERE dp.user_id = hp.user_id
                    AND dp.date = (hp.created_at::date + INTERVAL '14 days')::date
                    LIMIT 1
                ) AS actual_2w,
                
                -- Peso real al mes
                (
                    SELECT dp.weight_kg
                    FROM daily_progress dp
                    WHERE dp.user_id = hp.user_id
                    AND dp.date = (hp.created_at::date + INTERVAL '1 month')::date
                    LIMIT 1
                ) AS actual_1m
                
            FROM health_predictions hp
            WHERE hp.user_id = %s
            AND hp.created_at < NOW() - INTERVAL '2 weeks'
            ORDER BY hp.created_at DESC
            LIMIT 5
        """, (user_id,))
        
        stats = cursor.fetchall()
        
        if not stats:
            return {
                "has_stats": False,
                "message": "No hay suficiente historial para calcular estadísticas"
            }
        
        # Calcular precisión
        accuracy_data = []
        for stat in stats:
            stat_dict = dict(stat)
            
            accuracy = {}
            
            # Precisión a 2 semanas
            if stat_dict['actual_2w'] and stat_dict['pred_2w']:
                error_2w = abs(stat_dict['actual_2w'] - stat_dict['pred_2w'])
                accuracy_2w = max(0, 100 - (error_2w * 10))  # Penalizar 10% por kg de error
                accuracy['2_weeks'] = {
                    'predicted': float(stat_dict['pred_2w']),
                    'actual': float(stat_dict['actual_2w']),
                    'error_kg': float(error_2w),
                    'accuracy_pct': float(accuracy_2w)
                }
            
            # Precisión a 1 mes
            if stat_dict['actual_1m'] and stat_dict['pred_1m']:
                error_1m = abs(stat_dict['actual_1m'] - stat_dict['pred_1m'])
                accuracy_1m = max(0, 100 - (error_1m * 10))
                accuracy['1_month'] = {
                    'predicted': float(stat_dict['pred_1m']),
                    'actual': float(stat_dict['actual_1m']),
                    'error_kg': float(error_1m),
                    'accuracy_pct': float(accuracy_1m)
                }
            
            if accuracy:
                accuracy_data.append({
                    'prediction_id': stat_dict['id'],
                    'date': stat_dict['created_at'].isoformat(),
                    'accuracy': accuracy
                })
        
        # Calcular promedio de precisión
        all_accuracies = []
        for item in accuracy_data:
            for period in item['accuracy'].values():
                all_accuracies.append(period['accuracy_pct'])
        
        avg_accuracy = sum(all_accuracies) / len(all_accuracies) if all_accuracies else 0
        
        return {
            "has_stats": True,
            "predictions_analyzed": len(accuracy_data),
            "average_accuracy": round(avg_accuracy, 2),
            "details": accuracy_data
        }
# ============================================
# EJECUTAR
# ============================================
@app.get("/test-n8n")
def test_n8n_connection():
    """Endpoint de prueba para verificar conexión con n8n"""
    try:
        # Probar conexión básica
        response = requests.get("http://n8n:5678", timeout=5)
        n8n_status = f"✅ n8n alcanzable - Status: {response.status_code}"
    except Exception as e:
        n8n_status = f"❌ n8n NO alcanzable - Error: {str(e)}"
    
    try:
        # Probar webhook
        test_payload = {
            "user_id": 999,
            "age": 30,
            "weight": 70,
            "height": 170,
            "gender": "male",
            "activity_level": "moderate",
            "sleep_hours": 7,
            "smokes": False,
            "has_chronic_conditions": False,
            "health_goals": ["general_wellness"]
        }
        
        webhook_response = requests.post(
            "http://n8n:5678/webhook/health-assistant",
            json=test_payload,
            timeout=10
        )
        
        webhook_status = f"✅ Webhook respondió - Status: {webhook_response.status_code}"
        webhook_data = webhook_response.text[:200] if webhook_response.text else "VACÍO"
        
    except Exception as e:
        webhook_status = f"❌ Webhook falló - Error: {str(e)}"
        webhook_data = None
    
    return {
        "n8n_connection": n8n_status,
        "webhook_status": webhook_status,
        "webhook_response": webhook_data,
        "n8n_url": "http://n8n:5678/webhook/health-assistant"
    }
# ============================================
# ENDPOINTS DE REPORTES
# ============================================
from fastapi.responses import StreamingResponse
import io

@app.get("/api/reports/health/pdf")
def get_health_report_pdf(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de estado de salud en PDF"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT health_score, analyzed_at FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 5", (user_id,))
        history = [convert_to_json_serializable(dict(row)) for row in cursor.fetchall()]

    from advanced_reports import generate_risk_report_pdf
    pdf_buffer = generate_risk_report_pdf(analysis, profile, history, None, language)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_salud.pdf"}
    )

@app.get("/api/reports/health/excel")
def get_health_report_excel(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de estado de salud en Excel"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT health_score, analyzed_at, health_risk FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 10", (user_id,))
        history = [convert_to_json_serializable(dict(row)) for row in cursor.fetchall()]

    from advanced_reports import generate_risk_report_excel
    excel_buffer = generate_risk_report_excel(analysis, profile, history, language)
    excel_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_salud.xlsx"}
    )

@app.get("/api/reports/health/word")
def get_health_report_word(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de estado de salud en Word"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_risk_report_word
    word_buffer = generate_risk_report_word(analysis, profile, None, language)
    word_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(word_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=reporte_salud.docx"}
    )

# ==========================================
# ENDPOINTS DE PREDICCIONES
# ==========================================
@app.get("/api/reports/predictions/pdf")
def get_predictions_report_pdf(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de predicciones en PDF"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_predictions WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        prediction_row = cursor.fetchone()
        latest_prediction = convert_to_json_serializable(dict(prediction_row)) if prediction_row else None

    from advanced_reports import generate_predictions_report_pdf
    pdf_buffer = generate_predictions_report_pdf(analysis, profile, latest_prediction, language)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_predicciones.pdf"}
    )

@app.get("/api/reports/predictions/excel")
def get_predictions_report_excel(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de predicciones en Excel"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_predictions WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        prediction_row = cursor.fetchone()
        latest_prediction = convert_to_json_serializable(dict(prediction_row)) if prediction_row else None

    from advanced_reports import generate_predictions_report_excel
    excel_buffer = generate_predictions_report_excel(analysis, profile, latest_prediction, language)
    excel_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_predicciones.xlsx"}
    )

@app.get("/api/reports/predictions/word")
def get_predictions_report_word(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de predicciones en Word"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_predictions WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        prediction_row = cursor.fetchone()
        latest_prediction = convert_to_json_serializable(dict(prediction_row)) if prediction_row else None

    from advanced_reports import generate_predictions_report_word
    word_buffer = generate_predictions_report_word(analysis, profile, latest_prediction, language)
    word_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(word_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=reporte_predicciones.docx"}
    )

# ==========================================
# ENDPOINTS DE RECETAS
# ==========================================
@app.get("/api/reports/recipes/pdf")
def get_recipes_report_pdf(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de recetas en PDF"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_recipes_report_pdf
    pdf_buffer = generate_recipes_report_pdf(analysis, profile, language)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_recetas.pdf"}
    )

@app.get("/api/reports/recipes/excel")
def get_recipes_report_excel(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de recetas en Excel"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_recipes_report_excel
    excel_buffer = generate_recipes_report_excel(analysis, profile, language)
    excel_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_recetas.xlsx"}
    )

@app.get("/api/reports/recipes/word")
def get_recipes_report_word(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de recetas en Word"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_recipes_report_word
    word_buffer = generate_recipes_report_word(analysis, profile, language)
    word_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(word_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=reporte_recetas.docx"}
    )

# ==========================================
# ENDPOINTS DE EJERCICIO
# ==========================================
@app.get("/api/reports/exercise/pdf")
def get_exercise_report_pdf(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de ejercicio en PDF"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_exercise_report_pdf
    pdf_buffer = generate_exercise_report_pdf(analysis, profile, language)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_ejercicio.pdf"}
    )

@app.get("/api/reports/exercise/excel")
def get_exercise_report_excel(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de ejercicio en Excel"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_exercise_report_excel
    excel_buffer = generate_exercise_report_excel(analysis, profile, language)
    excel_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(excel_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_ejercicio.xlsx"}
    )

@app.get("/api/reports/exercise/word")
def get_exercise_report_word(user_id: int = Depends(verify_token), language: str = "es"):
    """Generar reporte de ejercicio en Word"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = %s", (user_id,))
        profile = convert_to_json_serializable(dict(cursor.fetchone()))
        
        cursor.execute("SELECT * FROM health_analyses WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        analysis = convert_to_json_serializable(dict(cursor.fetchone()))

    from advanced_reports import generate_exercise_report_word
    word_buffer = generate_exercise_report_word(analysis, profile, language)
    word_buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(word_buffer.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=reporte_ejercicio.docx"}
    )

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Health AI API Server con PostgreSQL + n8n")
    print("=" * 60)
    print(f"📊 Database: {DB_HOST}")
    print(f"🔗 n8n Webhook: {N8N_WEBHOOK_URL}")
    print("📚 Docs: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)