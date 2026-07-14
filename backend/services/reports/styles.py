"""
Styles — Traducciones, colores y constantes de estilo para reportes.

Módulo puro de datos. Sin lógica de negocio.
Sin dependencias de reportlab, xlsxwriter ni python-docx.
"""

# ==========================================
# TRADUCCIONES
# ==========================================

TRANSLATIONS = {
    "es": {
        "app_name": "HEALTH AI",
        "health_report": "Informe Clinico",
        "predictions_report": "Predicciones de Peso",
        "recipes_report": "Plan de Alimentacion",
        "exercise_report": "Plan de Ejercicio",
        "date_generated": "Fecha de Generacion",
        "patient": "Paciente",
        "health_score": "Puntuacion de Salud",
        "risk_level": "Nivel de Riesgo",
        "bmi": "IMC",
        "bmi_category": "Categoria IMC",
        "bmr": "Tasa Metabolica Basal",
        "tdee": "Gasto Energetico Diario",
        "fitness_level": "Nivel de Fitness",
        "nutrition_summary": "Resumen Nutricional",
        "daily_calories": "Calorias Diarias",
        "protein": "Proteinas",
        "carbs": "Carbohidratos",
        "fats": "Grasas",
        "meal": "Momento",
        "recipe": "Receta Sugerida",
        "protein_g": "Proteinas (g)",
        "breakfast": "Desayuno",
        "lunch": "Almuerzo",
        "dinner": "Cena",
        "snack": "Snack",
        "exercise_plan": "Plan de Ejercicio Semanal",
        "cardio": "Cardio",
        "strength": "Fuerza",
        "flexibility": "Flexibilidad",
        "duration": "Duracion/Frecuencia",
        "current_weight": "Peso Actual",
        "2_weeks": "2 Semanas",
        "1_month": "1 Mes",
        "6_months": "6 Meses",
        "weight": "Peso (kg)",
        "metric": "Metrica",
        "value": "Valor",
        "clinical_factors": "Factores de Riesgo Documentados",
        "type": "Tipo",
        "conditions": "Condiciones (Carga Negativa)",
        "chronic": "Enfermedades Cronicas",
        "genetic": "Riesgo Genetico Familiar",
        "no_data": "Ninguna registrada",
        "history": "Historial",
        "timeline": "Evolucion del Riesgo (Historico)",
        "indicator": "Indicador",
        "category": "Categoria",
        "detected_conditions": "Condiciones Detectadas",
        "genetics": "Genetica",
        "risk_evaluation": "Evaluacion de Riesgo Actual",
        "clinical_status": "Estado Clinico",
        "clinical_risk_report": "Informe de Riesgo Cardiovascular y Metabolico",
        "current_clinical_evaluation": "1. Evaluacion Clinica Actual",
        "calculated_risk": "Riesgo Calculado:",
        "factors_and_comorbidities": "2. Factores y Comorbilidades",
        "genetic_factors": "Factores Geneticos",
        "no_record": "Sin registro",
        "graph_projection": "3. Proyeccion Grafica",
        "weight_summary": "Resumen de Peso",
        "period": "Periodo",
        "nutrition_summary_1": "1. Resumen Nutricional",
        "suggested_recipes": "2. Recetas Sugeridas",
        "exercise_plan_1": "1. Plan de Ejercicio Semanal",
        "patient_evaluation": "Evaluacion del Paciente: Confidencial",
        "alerts": "Alertas Clinicas",
        "objectives": "Objetivos Semanales",
        "ml_prediction": "Prediccion del Modelo ML",
        "xai_explanation": "Explicacion del Analisis Inteligente",
        "confidence": "Confianza",
        "model": "Modelo",
        "scenario_follow": "Si sigue el plan",
        "scenario_ignore": "Si no sigue el plan",
        "projected_weight": "Peso Proyectado",
        "projected_bmi": "IMC Proyectado",
        "important_features": "Factores Mas Influyentes",
        "feature": "Factor",
        "importance": "Importancia",
        "narrative_summary": "Resumen Clinico",
        "narrative_bmi": "Interpretacion del IMC",
        "narrative_risk": "Interpretacion del Riesgo",
        "narrative_ml": "Interpretacion del Modelo ML",
        "narrative_recs": "Recomendaciones",
        "narrative_prognosis": "Pronostico",
        "high": "Alto",
        "medium": "Medio",
        "low": "Bajo",
    },
    "en": {
        "app_name": "HEALTH AI",
        "health_report": "Clinical Report",
        "predictions_report": "Weight Predictions",
        "recipes_report": "Nutrition Plan",
        "exercise_report": "Exercise Plan",
        "date_generated": "Generated Date",
        "patient": "Patient",
        "health_score": "Health Score",
        "risk_level": "Risk Level",
        "bmi": "BMI",
        "bmi_category": "BMI Category",
        "bmr": "Basal Metabolic Rate",
        "tdee": "Total Daily Energy Expenditure",
        "fitness_level": "Fitness Level",
        "nutrition_summary": "Nutrition Summary",
        "daily_calories": "Daily Calories",
        "protein": "Protein",
        "carbs": "Carbohydrates",
        "fats": "Fats",
        "meal": "Meal",
        "recipe": "Suggested Recipe",
        "protein_g": "Protein (g)",
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "snack": "Snack",
        "exercise_plan": "Weekly Exercise Plan",
        "cardio": "Cardio",
        "strength": "Strength",
        "flexibility": "Flexibility",
        "duration": "Duration/Frequency",
        "current_weight": "Current Weight",
        "2_weeks": "2 Weeks",
        "1_month": "1 Month",
        "6_months": "6 Months",
        "weight": "Weight (kg)",
        "metric": "Metric",
        "value": "Value",
        "clinical_factors": "Documented Risk Factors",
        "type": "Type",
        "conditions": "Conditions (Negative Load)",
        "chronic": "Chronic Diseases",
        "genetic": "Family Genetic Risk",
        "no_data": "None recorded",
        "history": "History",
        "timeline": "Risk Evolution (Historical)",
        "indicator": "Indicator",
        "category": "Category",
        "detected_conditions": "Detected Conditions",
        "genetics": "Genetics",
        "risk_evaluation": "Current Risk Evaluation",
        "clinical_status": "Clinical Status",
        "clinical_risk_report": "Cardiovascular and Metabolic Risk Report",
        "current_clinical_evaluation": "1. Current Clinical Evaluation",
        "calculated_risk": "Calculated Risk:",
        "factors_and_comorbidities": "2. Factors and Comorbidities",
        "genetic_factors": "Genetic Factors",
        "no_record": "No record",
        "graph_projection": "3. Graph Projection",
        "weight_summary": "Weight Summary",
        "period": "Period",
        "nutrition_summary_1": "1. Nutrition Summary",
        "suggested_recipes": "2. Suggested Recipes",
        "exercise_plan_1": "1. Weekly Exercise Plan",
        "patient_evaluation": "Patient Evaluation: Confidential",
        "alerts": "Clinical Alerts",
        "objectives": "Weekly Objectives",
        "ml_prediction": "ML Model Prediction",
        "xai_explanation": "Intelligent Analysis Explanation",
        "confidence": "Confidence",
        "model": "Model",
        "scenario_follow": "If you follow the plan",
        "scenario_ignore": "If you don't follow the plan",
        "projected_weight": "Projected Weight",
        "projected_bmi": "Projected BMI",
        "important_features": "Most Influential Factors",
        "feature": "Feature",
        "importance": "Importance",
        "narrative_summary": "Clinical Summary",
        "narrative_bmi": "BMI Interpretation",
        "narrative_risk": "Risk Interpretation",
        "narrative_ml": "ML Model Interpretation",
        "narrative_recs": "Recommendations",
        "narrative_prognosis": "Prognosis",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    },
}


def get_translations(language="es"):
    return TRANSLATIONS.get(language, TRANSLATIONS["es"])


# ==========================================
# COLORES POR NIVEL DE RIESGO
# ==========================================

RISK_COLORS = {
    "critical": {"hex": "#e74c3c", "rgb": (231, 76, 60), "name": "Critico"},
    "high": {"hex": "#e67e22", "rgb": (230, 126, 34), "name": "En Riesgo"},
    "medium": {"hex": "#f1c40f", "rgb": (241, 196, 15), "name": "Aceptable"},
    "low": {"hex": "#2ecc71", "rgb": (46, 204, 113), "name": "Bueno"},
    "optimal": {"hex": "#2ecc71", "rgb": (46, 204, 113), "name": "Optimo"},
}

RISK_KEYWORD_MAP = {
    "Critico": "critical",
    "Critical": "critical",
    "En Riesgo": "high",
    "At Risk": "high",
    "Aceptable": "medium",
    "Acceptable": "medium",
    "Bueno": "low",
    "Good": "low",
}


def get_risk_colors(risk_level):
    """Retorna colores segun el nivel de riesgo."""
    if not risk_level:
        return {"hex": "#7f8c8d", "rgb": (127, 140, 141), "name": "Sin Datos"}

    for keyword, key in RISK_KEYWORD_MAP.items():
        if keyword in str(risk_level):
            return RISK_COLORS[key]

    return {"hex": "#7f8c8d", "rgb": (127, 140, 141), "name": "Sin Datos"}


# ==========================================
# COLORES POR PRIORIDAD DE ALERTA
# ==========================================

ALERT_PRIORITY_COLORS = {
    "high": {"hex": "#e74c3c", "rgb": (231, 76, 60), "label_en": "HIGH", "label_es": "ALTA"},
    "medium": {"hex": "#f39c12", "rgb": (243, 156, 18), "label_en": "MEDIUM", "label_es": "MEDIA"},
    "low": {"hex": "#3498db", "rgb": (52, 152, 219), "label_en": "LOW", "label_es": "BAJA"},
}


# ==========================================
# COLORES GENERALES
# ==========================================

COLORS = {
    "primary_dark": "#2c3e50",
    "primary_medium": "#34495e",
    "background_light": "#ecf0f1",
    "white": "#ffffff",
    "black": "#000000",
    "text_dark": "#2c3e50",
    "text_light": "#7f8c8d",
    "success": "#2ecc71",
    "warning": "#f1c40f",
    "danger": "#e74c3c",
    "info": "#3498db",
}


# ==========================================
# MAPEO BMI
# ==========================================

BMI_CATEGORY_LABELS = {
    "severely_underweight": "Desnutricion severa",
    "underweight": "Bajo peso",
    "normal": "Peso normal",
    "overweight": "Sobrepeso",
    "obese_1": "Obesidad grado I",
    "obese_2_3": "Obesidad grado II/III",
}

BMI_CATEGORY_COLORS = {
    "severely_underweight": "#e74c3c",
    "underweight": "#e67e22",
    "normal": "#2ecc71",
    "overweight": "#f1c40f",
    "obese_1": "#e67e22",
    "obese_2_3": "#e74c3c",
}
