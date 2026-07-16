-- Agregar columnas para almacenar ml_prediction y xai en health_analyses
ALTER TABLE health_analyses
ADD COLUMN IF NOT EXISTS ml_prediction JSONB,
ADD COLUMN IF NOT EXISTS xai JSONB;
