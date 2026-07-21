-- Migración para agregar campos ml_prediction y xai a la tabla health_analyses
-- Ejecutar este script en bases de datos existentes

-- Verificar si los campos ya existen antes de agregarlos
DO $$
BEGIN
    -- Agregar campo ml_prediction si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'health_analyses' 
        AND column_name = 'ml_prediction'
    ) THEN
        ALTER TABLE health_analyses ADD COLUMN ml_prediction JSONB;
        RAISE NOTICE 'Campo ml_prediction agregado exitosamente';
    ELSE
        RAISE NOTICE 'Campo ml_prediction ya existe';
    END IF;

    -- Agregar campo xai si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'health_analyses' 
        AND column_name = 'xai'
    ) THEN
        ALTER TABLE health_analyses ADD COLUMN xai JSONB;
        RAISE NOTICE 'Campo xai agregado exitosamente';
    ELSE
        RAISE NOTICE 'Campo xai ya existe';
    END IF;
END $$;
