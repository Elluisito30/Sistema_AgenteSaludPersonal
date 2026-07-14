"""
Health Score Rules — Cálculo del puntaje de salud con tablas de reglas.

El puntaje se calcula desde 100 restando penalizaciones configurables.
Cada regla es un diccionario con condición, penalización y opcionalmente un tope.
"""


# ──────────────────────────────────────────────
# Reglas de penalización por BMI
# ──────────────────────────────────────────────

BMI_SCORE_RULES = [
    {
        "condition": lambda bmi, _: bmi < 16,
        "penalty": 35,
        "cap": 40,
        "label": "Desnutrición severa",
    },
    {
        "condition": lambda bmi, _: 16 <= bmi < 18.5,
        "penalty": 20,
        "cap": None,
        "label": "Bajo peso",
    },
    {
        "condition": lambda bmi, _: 25 <= bmi < 30,
        "penalty": 15,
        "cap": None,
        "label": "Sobrepeso",
    },
    {
        "condition": lambda bmi, _: 30 <= bmi < 35,
        "penalty": 25,
        "cap": None,
        "label": "Obesidad I",
    },
    {
        "condition": lambda bmi, _: bmi >= 35,
        "penalty": 40,
        "cap": 40,
        "label": "Obesidad II/III",
    },
]

# ──────────────────────────────────────────────
# Reglas de penalización por estilo de vida
# ──────────────────────────────────────────────

LIFESTYLE_SCORE_RULES = [
    {
        "condition": lambda _, p: p.get("smokes", False),
        "penalty": 20,
        "label": "Tabaquismo",
    },
    {
        "condition": lambda _, p: p.get("sleep_hours", 7) < 6,
        "penalty": 8,
        "label": "Sueño insuficiente",
    },
    {
        "condition": lambda _, p: p.get("sleep_hours", 7) > 9,
        "penalty": 3,
        "label": "Sueño excesivo",
    },
    {
        "condition": lambda _, p: p.get("activity_level", "moderate") in ["sedentary", "none", "sedentario"],
        "penalty": 10,
        "label": "Sedentarismo",
    },
]

# ──────────────────────────────────────────────
# Reglas de penalización por enfermedades crónicas
# ──────────────────────────────────────────────

DISEASE_SCORE_RULES = [
    {
        "keywords": ["diabetes"],
        "penalty": 25,
        "label": "Diabetes",
        "special_cap": {"condition": "smokes", "cap": 45},
    },
    {
        "keywords": ["hipertensión", "hipertension"],
        "penalty": 15,
        "label": "Hipertensión",
    },
    {
        "keywords": ["colesterol"],
        "penalty": 10,
        "label": "Colesterol alto",
    },
]

# ──────────────────────────────────────────────
# Reglas de penalización por genética
# ──────────────────────────────────────────────

GENETIC_SCORE_RULES = [
    {
        "condition": lambda risk_factors: len(risk_factors or []) > 0,
        "penalty": 10,
        "label": "Factores de riesgo genético",
    },
]

# ──────────────────────────────────────────────
# Clasificación del puntaje final
# ──────────────────────────────────────────────

SCORE_RISK_LABELS = [
    {"max_score": 20, "label": "Crítico - Requiere atención médica URGENTE", "level": "critical"},
    {"max_score": 40, "label": "Alto Riesgo - Consulta a tu médico de cabecera", "level": "high"},
    {"max_score": 60, "label": "Riesgo Moderado - Mejora tus hábitos", "level": "medium"},
    {"max_score": 80, "label": "Aceptable - Mantén tus hábitos saludables", "level": "low"},
    {"max_score": 100, "label": "Buen estado - Sigue así", "level": "optimal"},
]

# ──────────────────────────────────────────────
# Mapeo SEVERITY → health_risk (fuente única)
# ──────────────────────────────────────────────

SEVERITY_RISK_MAP = {
    "critical": {
        "risk_label": "Crítico - Requiere atención médica URGENTE",
        "risk_level": "critical",
    },
    "high": {
        "risk_label": "Alto Riesgo - Consulta a tu médico de cabecera",
        "risk_level": "high",
    },
    "medium": {
        "risk_label": "Riesgo Moderado - Mejora tus hábitos",
        "risk_level": "medium",
    },
    "low": {
        "risk_label": "Aceptable - Mantén tus hábitos saludables",
        "risk_level": "low",
    },
}

# ──────────────────────────────────────────────
# Nivel de fitness basado en puntaje
# ──────────────────────────────────────────────

FITNESS_LEVELS = [
    {"min_score": 80, "level": "advanced"},
    {"min_score": 60, "level": "intermediate"},
    {"min_score": 0, "level": "beginner"},
]


def calculate_health_score(bmi: float, profile: dict, severity: str = None) -> dict:
    """
    Calcula el puntaje de salud desde 100 con penalizaciones.

    El risk_level y risk_label se derivan del severity (fuente única de verdad).
    El score numérico es una métrica cuantitativa independiente.

    Args:
        bmi: IMC calculado del paciente
        profile: dict con smokes, sleep_hours, activity_level,
                 chronic_diseases, genetic_risk_factors
        severity: severidad compuesta calculada por compute_composite_severity()

    Returns:
        dict con score, risk_label, risk_level, fitness_level, applied_penalties
    """
    score = 100
    applied_penalties = []
    has_penalties = False
    has_diabetes = False

    # 1. Penalizaciones por BMI
    for rule in BMI_SCORE_RULES:
        if rule["condition"](bmi, profile):
            score -= rule["penalty"]
            has_penalties = True
            applied_penalties.append({"factor": rule["label"], "penalty": rule["penalty"]})
            if rule.get("cap") and score > rule["cap"]:
                score = rule["cap"]
            break

    # 2. Penalizaciones por estilo de vida
    for rule in LIFESTYLE_SCORE_RULES:
        if rule["condition"](bmi, profile):
            score -= rule["penalty"]
            has_penalties = True
            applied_penalties.append({"factor": rule["label"], "penalty": rule["penalty"]})

    # 3. Penalizaciones por enfermedades crónicas
    chronic_diseases = profile.get("chronic_diseases", []) or []
    for disease in chronic_diseases:
        disease_lower = disease.lower()
        for rule in DISEASE_SCORE_RULES:
            if any(kw in disease_lower for kw in rule["keywords"]):
                score -= rule["penalty"]
                has_penalties = True
                applied_penalties.append({"factor": rule["label"], "penalty": rule["penalty"]})
                if "diabetes" in disease_lower:
                    has_diabetes = True
                break

    # 4. Penalizaciones por genética
    genetic_risk_factors = profile.get("genetic_risk_factors", []) or []
    for rule in GENETIC_SCORE_RULES:
        if rule["condition"](genetic_risk_factors):
            score -= rule["penalty"]
            has_penalties = True
            applied_penalties.append({"factor": rule["label"], "penalty": rule["penalty"]})

    # 5. Tope compuesto: diabetes + tabaquismo
    if has_diabetes and profile.get("smokes", False):
        if score > 45:
            score = 45

    # 6. Clamp final
    score = max(0, min(100, score))

    # 7. Clasificación de riesgo — derivada del severity (fuente única)
    severity_key = severity if severity in SEVERITY_RISK_MAP else "low"
    risk_info = SEVERITY_RISK_MAP[severity_key]
    risk_label = risk_info["risk_label"]
    risk_level = risk_info["risk_level"]

    # 8. Nivel de fitness — derivado del score (cuantitativo)
    fitness_level = "beginner"
    for fl in FITNESS_LEVELS:
        if score >= fl["min_score"]:
            fitness_level = fl["level"]
            break

    return {
        "score": score,
        "risk_label": risk_label,
        "risk_level": risk_level,
        "fitness_level": fitness_level,
        "applied_penalties": applied_penalties,
    }
