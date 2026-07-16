-- Persistir predicción ML y XAI junto al análisis
ALTER TABLE health_analyses ADD COLUMN IF NOT EXISTS ml_prediction JSONB;
ALTER TABLE health_analyses ADD COLUMN IF NOT EXISTS xai JSONB;
