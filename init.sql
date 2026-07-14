-- ============================================
-- HEALTH AI SYSTEM - DATABASE SCHEMA
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS health_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female')),
    height_cm DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    activity_level VARCHAR(20),
    sleep_hours INTEGER,
    smokes BOOLEAN DEFAULT FALSE,
    has_chronic_conditions BOOLEAN DEFAULT FALSE,
    genetics_risk VARCHAR(50) DEFAULT 'low',
    chronic_conditions_detail TEXT,
    health_goals TEXT[],
    chronic_diseases TEXT[],
    genetic_risk_factors TEXT[],
    family_history BOOLEAN DEFAULT FALSE,
    favc VARCHAR(20) DEFAULT 'Sometimes',
    fcvc DECIMAL(3,1) DEFAULT 2.0,
    ch2o DECIMAL(3,1) DEFAULT 2.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS health_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    bmi DECIMAL(5,2),
    bmi_category VARCHAR(20),
    bmr DECIMAL(7,2),
    tdee DECIMAL(7,2),
    health_score DECIMAL(5,2),
    health_risk VARCHAR(20),
    fitness_level VARCHAR(20),
    health_plan JSONB,
    nutrient_recommendations JSONB,
    predicted_improvements JSONB,
    alerts JSONB,
    weekly_goals TEXT[],
    analyzed_at TIMESTAMP DEFAULT NOW(),
    next_checkup DATE,
    confidence_score DECIMAL(5,2)
);

CREATE INDEX IF NOT EXISTS idx_analyses_user ON health_analyses(user_id, id DESC);

CREATE TABLE IF NOT EXISTS daily_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    weight_kg DECIMAL(5,2),
    steps_count INTEGER,
    exercise_minutes INTEGER,
    calories_consumed DECIMAL(7,2),
    protein_g DECIMAL(6,2),
    carbs_g DECIMAL(6,2),
    fats_g DECIMAL(6,2),
    water_liters DECIMAL(4,2),
    sleep_hours DECIMAL(3,1),
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 10),
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    mood INTEGER CHECK (mood BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_progress_user ON daily_progress(user_id, date DESC);

CREATE TABLE IF NOT EXISTS health_predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    analysis_id INTEGER REFERENCES health_analyses(id) ON DELETE SET NULL,
    profile_snapshot JSONB,
    predictions_data JSONB,
    model_used VARCHAR(50),
    confidence_score DECIMAL(5,4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_user ON health_predictions(user_id, id DESC);
