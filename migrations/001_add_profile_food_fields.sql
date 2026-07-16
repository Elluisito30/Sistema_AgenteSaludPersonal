-- Campos de hábitos alimenticios y antecedentes familiares (onboarding paso 5-6)
ALTER TABLE health_profiles ADD COLUMN IF NOT EXISTS family_history BOOLEAN DEFAULT FALSE;
ALTER TABLE health_profiles ADD COLUMN IF NOT EXISTS favc VARCHAR(20) DEFAULT 'Sometimes';
ALTER TABLE health_profiles ADD COLUMN IF NOT EXISTS fcvc DECIMAL(3,1) DEFAULT 2.0;
ALTER TABLE health_profiles ADD COLUMN IF NOT EXISTS ch2o DECIMAL(3,1) DEFAULT 2.0;
