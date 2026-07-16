-- Change weekly_goals to JSONB
ALTER TABLE health_analyses
    ALTER COLUMN weekly_goals TYPE JSONB USING weekly_goals::jsonb;
