-- Make health_analyses columns longer
ALTER TABLE health_analyses
    ALTER COLUMN bmi_category TYPE VARCHAR(50),
    ALTER COLUMN health_risk TYPE VARCHAR(100),
    ALTER COLUMN fitness_level TYPE VARCHAR(50);
