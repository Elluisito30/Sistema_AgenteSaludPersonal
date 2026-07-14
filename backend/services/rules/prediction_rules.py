"""
Prediction Rules — Proyecciones de peso basadas en categoría BMI, objetivos y perfil.

Estrategias de predicción con soporte futuro para resultados ML.
"""


# ──────────────────────────────────────────────
# Estrategias de cambio semanal por categoría BMI
# ──────────────────────────────────────────────

BMI_PREDICTION_STRATEGIES = {
    "severely_underweight": {
        "base_weekly_change_kg": 0.30,
        "goal_adjustments": {
            "muscle_gain": 0.35,
            "weight_loss": 0.0,
        },
        "max_change_per_week": 0.5,
        "note": "Ganancia progresiva supervisada. Consulta médica recomendada.",
        "model_used": "clinical_rule_v2_underweight",
    },
    "underweight": {
        "base_weekly_change_kg": 0.25,
        "goal_adjustments": {
            "muscle_gain": 0.30,
            "weight_loss": 0.0,
        },
        "max_change_per_week": 0.4,
        "note": "Ganancia gradual hacia peso saludable.",
        "model_used": "clinical_rule_v2_underweight",
    },
    "normal": {
        "base_weekly_change_kg": 0.0,
        "goal_adjustments": {
            "weight_loss": -0.35,
            "muscle_gain": 0.25,
            "better_sleep": 0.0,
            "energy_boost": 0.0,
            "stress_reduction": 0.0,
            "general_wellness": 0.0,
        },
        "max_change_per_week": 0.5,
        "note": "Proyección basada en tus objetivos actuales.",
        "model_used": "clinical_rule_v2_normal",
    },
    "overweight": {
        "base_weekly_change_kg": -0.10,
        "goal_adjustments": {
            "weight_loss": -0.40,
            "muscle_gain": -0.10,
        },
        "max_change_per_week": 0.5,
        "note": "Pérdida progresiva recomendada para resultados sostenibles.",
        "model_used": "clinical_rule_v2_overweight",
    },
    "obese_1": {
        "base_weekly_change_kg": -0.20,
        "goal_adjustments": {
            "weight_loss": -0.50,
            "muscle_gain": -0.15,
        },
        "max_change_per_week": 0.75,
        "note": "Pérdida de peso supervisada. No exceder 1 kg por semana.",
        "model_used": "clinical_rule_v2_obese",
    },
    "obese_2_3": {
        "base_weekly_change_kg": -0.30,
        "goal_adjustments": {
            "weight_loss": -0.60,
            "muscle_gain": -0.20,
        },
        "max_change_per_week": 1.0,
        "note": "Pérdida de peso con supervisión médica. Resultados iniciales pueden ser más rápidos.",
        "model_used": "clinical_rule_v2_obese",
    },
}

# ──────────────────────────────────────────────
# Calidad de predicción por fuente
# ──────────────────────────────────────────────

PREDICTION_CONFIDENCE = {
    "clinical_rule_v2_underweight": 0.75,
    "clinical_rule_v2_normal": 0.80,
    "clinical_rule_v2_overweight": 0.80,
    "clinical_rule_v2_obese": 0.75,
    "ml_model_xgboost": 0.96,
    "ml_model_mlp": 0.95,
    "ml_model_rf": 0.95,
    "ml_model_logreg": 0.88,
    "ml_ensemble": 0.97,
}


def generate_predictions(
    weight_kg: float,
    bmi_category: str,
    goals: list,
    ml_prediction: dict = None,
) -> dict:
    """
    Genera proyecciones de peso a 2 semanas, 1 mes y 6 meses.

    Args:
        weight_kg: peso actual en kg
        bmi_category: categoría BMI
        goals: lista de objetivos del paciente
        ml_prediction: resultado futuro del modelo ML (opcional)
            {predicted_class, probabilities, confidence}

    Returns:
        dict compatible con el frontend: predictions_data, model_used, confidence_score
    """
    strategy = BMI_PREDICTION_STRATEGIES.get(
        bmi_category, BMI_PREDICTION_STRATEGIES["normal"]
    )

    # Calcular cambio semanal
    weekly_change = strategy["base_weekly_change_kg"]
    for goal in goals:
        goal_adj = strategy["goal_adjustments"].get(goal)
        if goal_adj is not None:
            weekly_change = goal_adj
            break

    # Aplicar límite de cambio semanal
    max_change = strategy["max_change_per_week"]
    weekly_change = max(-max_change, min(max_change, weekly_change))

    # Si hay predicción ML, usarla como referencia
    model_used = strategy["model_used"]
    confidence = PREDICTION_CONFIDENCE.get(model_used, 0.80)

    if ml_prediction and ml_prediction.get("confidence", 0) > 70:
        ml_class = ml_prediction.get("predicted_class", "")
        ml_confidence = ml_prediction.get("confidence", 0) / 100.0

        ml_strategies = {
            "Insufficient_Weight": 0.30,
            "Normal_Weight": 0.0,
            "Overweight_Level_I": -0.35,
            "Overweight_Level_II": -0.40,
            "Obesity_Type_I": -0.50,
            "Obesity_Type_II": -0.55,
            "Obesity_Type_III": -0.60,
        }

        ml_weekly = ml_strategies.get(ml_class, weekly_change)

        weight_ml = ml_confidence
        weight_rules = 1.0 - ml_confidence
        weekly_change = (ml_weekly * weight_ml) + (weekly_change * weight_rules)

        model_used = f"hybrid_rule+ml({ml_prediction.get('model_used', 'unknown')})"
        confidence = max(confidence, ml_confidence * 0.95)

    # Calcular proyecciones
    two_weeks = round(weight_kg + (weekly_change * 2), 1)
    one_month = round(weight_kg + (weekly_change * 4), 1)
    six_months = round(weight_kg + (weekly_change * 24), 1)

    two_weeks = max(30.0, two_weeks)
    one_month = max(30.0, one_month)
    six_months = max(30.0, six_months)

    predictions_data = {
        "predictions": {
            "2_weeks": {"weight_kg": two_weeks},
            "1_month": {"weight_kg": one_month},
            "6_months": {"weight_kg": six_months},
        }
    }

    return {
        "predictions_data": predictions_data,
        "model_used": model_used,
        "confidence_score": round(confidence, 2),
        "note": strategy.get("note", ""),
    }
