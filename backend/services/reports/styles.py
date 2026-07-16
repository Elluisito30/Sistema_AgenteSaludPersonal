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
        "metrics": "Metricas",
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
        "objective": "Objetivo",
        "ml_prediction": "Prediccion del Modelo ML",
        "xai_explanation": "Explicacion del Analisis Inteligente",
        "confidence": "Confianza",
        "model": "Modelo",
        "classification": "Clasificacion",
        "scenarios": "Escenarios",
        "scenario_follow": "Si sigue el plan",
        "scenario_ignore": "Si no sigue el plan",
        "projected_weight": "Peso Proyectado",
        "projected_bmi": "IMC Proyectado",
        "projected_weight_label": "Peso proyectado",
        "important_features": "Factores Mas Influyentes",
        "feature": "Factor",
        "importance": "Importancia",
        "narrative_summary": "Resumen Clinico",
        "narrative_bmi": "Interpretacion del IMC",
        "narrative_risk": "Interpretacion del Riesgo",
        "narrative_ml": "Interpretacion del Modelo ML",
        "narrative_recs": "Recomendaciones",
        "narrative_prognosis": "Pronostico",
        "narratives": "Narrativas",
        "section": "Seccion",
        "text": "Texto",
        "message": "Mensaje",
        "date": "Fecha",
        "no_projection_data": "No hay datos de proyeccion disponibles.",
        "high": "Alto",
        "medium": "Medio",
        "low": "Bajo",
        "confidence_high": "alta",
        "confidence_medium": "media",
        "confidence_low": "baja",
        "confidence_very_low": "muy baja",
        "risk_critical": "Critico",
        "risk_high": "En Riesgo",
        "risk_medium": "Aceptable",
        "risk_low": "Bueno",
        "risk_optimal": "Optimo",
        "risk_unknown": "Sin Datos",
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
        "metrics": "Metrics",
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
        "objective": "Objective",
        "ml_prediction": "ML Model Prediction",
        "xai_explanation": "Intelligent Analysis Explanation",
        "confidence": "Confidence",
        "model": "Model",
        "classification": "Classification",
        "scenarios": "Scenarios",
        "scenario_follow": "If you follow the plan",
        "scenario_ignore": "If you don't follow the plan",
        "projected_weight": "Projected Weight",
        "projected_bmi": "Projected BMI",
        "projected_weight_label": "Projected weight",
        "important_features": "Most Influential Factors",
        "feature": "Feature",
        "importance": "Importance",
        "narrative_summary": "Clinical Summary",
        "narrative_bmi": "BMI Interpretation",
        "narrative_risk": "Risk Interpretation",
        "narrative_ml": "ML Model Interpretation",
        "narrative_recs": "Recommendations",
        "narrative_prognosis": "Prognosis",
        "narratives": "Narratives",
        "section": "Section",
        "text": "Text",
        "message": "Message",
        "date": "Date",
        "no_projection_data": "No projection data available.",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "confidence_high": "high",
        "confidence_medium": "medium",
        "confidence_low": "low",
        "confidence_very_low": "very low",
        "risk_critical": "Critical",
        "risk_high": "At Risk",
        "risk_medium": "Acceptable",
        "risk_low": "Good",
        "risk_optimal": "Optimal",
        "risk_unknown": "No Data",
    },
}


def get_translations(language="es"):
    return TRANSLATIONS.get(language, TRANSLATIONS["es"])


# ==========================================
# COLORES POR NIVEL DE RIESGO
# ==========================================

RISK_COLORS = {
    "critical": {"hex": "#e74c3c", "rgb": (231, 76, 60)},
    "high": {"hex": "#e67e22", "rgb": (230, 126, 34)},
    "medium": {"hex": "#f1c40f", "rgb": (241, 196, 15)},
    "low": {"hex": "#2ecc71", "rgb": (46, 204, 113)},
    "optimal": {"hex": "#2ecc71", "rgb": (46, 204, 113)},
}

RISK_LEVEL_LABELS = {
    "critical": {"es": "Critico", "en": "Critical"},
    "high": {"es": "En Riesgo", "en": "At Risk"},
    "medium": {"es": "Aceptable", "en": "Acceptable"},
    "low": {"es": "Bueno", "en": "Good"},
    "optimal": {"es": "Optimo", "en": "Optimal"},
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
    "Optimo": "optimal",
    "Optimal": "optimal",
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "optimal": "optimal",
}


def resolve_risk_key(risk_level):
    """Normaliza un nivel de riesgo a clave canónica (critical/high/medium/low/optimal)."""
    if not risk_level:
        return None
    text = str(risk_level)
    for keyword, key in RISK_KEYWORD_MAP.items():
        if keyword.lower() in text.lower() or keyword == text:
            return key
    lower = text.lower().strip()
    if lower in RISK_COLORS:
        return lower
    return None


def get_risk_label(risk_level, language="es"):
    """Label traducido para un nivel de riesgo."""
    key = resolve_risk_key(risk_level)
    lang = language if language in ("es", "en") else "es"
    if key and key in RISK_LEVEL_LABELS:
        return RISK_LEVEL_LABELS[key][lang]
    t = get_translations(lang)
    return t["risk_unknown"]


def get_risk_colors(risk_level, language="es"):
    """Retorna colores segun el nivel de riesgo, con label traducido."""
    key = resolve_risk_key(risk_level)
    lang = language if language in ("es", "en") else "es"
    if key and key in RISK_COLORS:
        colors = dict(RISK_COLORS[key])
        colors["name"] = RISK_LEVEL_LABELS[key][lang]
        colors["key"] = key
        return colors
    t = get_translations(lang)
    return {"hex": "#7f8c8d", "rgb": (127, 140, 141), "name": t["risk_unknown"], "key": None}


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
    "primary_accent": "#1abc9c",
    "background_light": "#ecf0f1",
    "background_soft": "#f7f9fb",
    "grid_soft": "#d5dbe3",
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
    "severely_underweight": {"es": "Desnutricion severa", "en": "Severely underweight"},
    "underweight": {"es": "Bajo peso", "en": "Underweight"},
    "normal": {"es": "Peso normal", "en": "Normal weight"},
    "overweight": {"es": "Sobrepeso", "en": "Overweight"},
    "obese_1": {"es": "Obesidad grado I", "en": "Obesity class I"},
    "obese_2_3": {"es": "Obesidad grado II/III", "en": "Obesity class II/III"},
}

BMI_CATEGORY_COLORS = {
    "severely_underweight": "#e74c3c",
    "underweight": "#e67e22",
    "normal": "#2ecc71",
    "overweight": "#f1c40f",
    "obese_1": "#e67e22",
    "obese_2_3": "#e74c3c",
}


def get_bmi_category_label(category, language="es"):
    """Retorna la etiqueta BMI traducida para la categoría dada."""
    lang = language if language in ("es", "en") else "es"
    entry = BMI_CATEGORY_LABELS.get(category)
    if not entry:
        return category or ""
    if isinstance(entry, dict):
        return entry.get(lang) or entry.get("es") or category
    return entry
