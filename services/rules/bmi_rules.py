"""
BMI Rules — Clasificación de IMC, categorías OMS y mapeo de severidad clínica.

Estructuras de datos reutilizables para todas las demás reglas.
Todo el sistema de severidad se deriva de estas tablas.
"""

# ──────────────────────────────────────────────
# Tabla maestra de categorías BMI (OMS)
# ──────────────────────────────────────────────

BMI_CATEGORIES = {
    "severely_underweight": {
        "min": 0,
        "max": 16,
        "label": "Desnutrición severa",
        "label_short": "Desnutrición",
        "description": "IMC por debajo de 16 indica desnutrición severa que requiere intervención médica inmediata.",
        "who_code": "SEVERE_THINNESS",
    },
    "underweight": {
        "min": 16,
        "max": 18.5,
        "label": "Bajo peso",
        "label_short": "Bajo peso",
        "description": "IMC entre 16 y 18.5 indica peso insuficiente. Se recomienda valoración nutricional.",
        "who_code": "THINNESS",
    },
    "normal": {
        "min": 18.5,
        "max": 25,
        "label": "Peso normal",
        "label_short": "Normal",
        "description": "IMC dentro del rango saludable. Mantener hábitos actuales.",
        "who_code": "NORMAL",
    },
    "overweight": {
        "min": 25,
        "max": 30,
        "label": "Sobrepeso",
        "label_short": "Sobrepeso",
        "description": "IMC entre 25 y 30 indica sobrepeso. Se sugiere ajuste en dieta y actividad física.",
        "who_code": "PRE_OBESE",
    },
    "obese_1": {
        "min": 30,
        "max": 35,
        "label": "Obesidad grado I",
        "label_short": "Obesidad I",
        "description": "IMC entre 30 y 35 indica obesidad grado I. Se requiere intervención nutricional y control médico.",
        "who_code": "OBESE_I",
    },
    "obese_2_3": {
        "min": 35,
        "max": 100,
        "label": "Obesidad grado II/III",
        "label_short": "Obesidad II/III",
        "description": "IMC mayor a 35 indica obesidad severa. Intervención médica urgente necesaria.",
        "who_code": "OBESE_II_III",
    },
}

# ──────────────────────────────────────────────
# Mapeo de severidad por categoría BMI
# ──────────────────────────────────────────────

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

SEVERITY_BY_BMI_CATEGORY = {
    "severely_underweight": "critical",
    "underweight": "high",
    "normal": "low",
    "overweight": "medium",
    "obese_1": "high",
    "obese_2_3": "critical",
}

# ──────────────────────────────────────────────
# Impacto de enfermedades crónicas en severidad
# ──────────────────────────────────────────────

DISEASE_SEVERITY_BOOST = {
    "diabetes": {"boost": 1, "max_severity": "critical"},
    "hipertensión": {"boost": 1, "max_severity": "critical"},
    "hipertension": {"boost": 1, "max_severity": "critical"},
    "colesterol": {"boost": 0, "max_severity": "high"},
}

# ──────────────────────────────────────────────
# Impacto de factores de estilo de vida
# ──────────────────────────────────────────────

LIFESTYLE_SEVERITY_BOOST = {
    "smoking": {"boost": 1, "max_severity": "critical"},
    "sedentary": {"boost": 0, "max_severity": "medium"},
    "poor_sleep": {"boost": 0, "max_severity": "medium"},
}


def classify_bmi(bmi: float) -> str:
    """Clasifica el BMI en una categoría usando la tabla OMS."""
    for category, config in BMI_CATEGORIES.items():
        if config["min"] <= bmi < config["max"]:
            return category
    return "obese_2_3"


def get_bmi_info(bmi_category: str) -> dict:
    """Retorna la información completa de una categoría BMI."""
    return BMI_CATEGORIES.get(bmi_category, BMI_CATEGORIES["normal"])


def compute_composite_severity(
    bmi_category: str,
    chronic_diseases: list = None,
    smokes: bool = False,
    activity_level: str = "moderate",
    sleep_hours: int = 7,
) -> str:
    """
    Calcula la severidad compuesta considerando BMI + factores adicionales.
    Prioridad: chronic diseases > smoking > BMI base.
    """
    severity = SEVERITY_BY_BMI_CATEGORY.get(bmi_category, "low")
    severity_idx = SEVERITY_LEVELS.index(severity)

    if smokes:
        boost = LIFESTYLE_SEVERITY_BOOST["smoking"]["boost"]
        new_idx = min(severity_idx + boost, len(SEVERITY_LEVELS) - 1)
        severity_idx = new_idx

    if activity_level in ["sedentary", "none", "sedentario"]:
        boost = LIFESTYLE_SEVERITY_BOOST["sedentary"]["boost"]
        new_idx = min(severity_idx + boost, len(SEVERITY_LEVELS) - 1)
        severity_idx = new_idx

    if sleep_hours < 6:
        boost = LIFESTYLE_SEVERITY_BOOST["poor_sleep"]["boost"]
        new_idx = min(severity_idx + boost, len(SEVERITY_LEVELS) - 1)
        severity_idx = new_idx

    for disease in (chronic_diseases or []):
        disease_lower = disease.lower()
        for key, config in DISEASE_SEVERITY_BOOST.items():
            if key in disease_lower:
                boost = config["boost"]
                if boost > 0:
                    new_idx = min(severity_idx + boost, len(SEVERITY_LEVELS) - 1)
                    severity_idx = new_idx
                break

    return SEVERITY_LEVELS[severity_idx]
