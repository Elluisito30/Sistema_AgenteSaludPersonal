"""
Alert Rules — Generación dinámica de alertas clínicas basada en el perfil del paciente.

Cada categoría BMI tiene sus propias alertas base.
Se añaden alertas modulares por condición, estilo de vida y genética.
"""


# ──────────────────────────────────────────────
# Alertas base por categoría BMI
# ──────────────────────────────────────────────

BMI_ALERTS = {
    "severely_underweight": [
        {
            "priority": "critical",
            "message": "🚨 Alerta Clínica: Tu IMC indica desnutrición severa. Se requiere valoración médica URGENTE.",
            "category": "nutritional",
        },
        {
            "priority": "high",
            "message": "🏥 Consulta inmediata con nutricionista y médico general es indispensable.",
            "category": "medical",
        },
        {
            "priority": "high",
            "message": "⚠️ No se recomienda ninguna dieta de pérdida de peso. Tu prioridad es recuperar un peso saludable.",
            "category": "nutritional",
        },
    ],
    "underweight": [
        {
            "priority": "high",
            "message": "⚠️ Alerta: Tu peso está por debajo del rango saludable. Se recomienda valoración con nutricionista.",
            "category": "nutritional",
        },
        {
            "priority": "medium",
            "message": "📋 Un plan de alimentación con superávit calórico puede ayudarte a alcanzar un peso saludable.",
            "category": "nutritional",
        },
    ],
    "normal": [
        {
            "priority": "low",
            "message": "✅ Tu IMC está dentro del rango saludable. Mantén tus hábitos actuales.",
            "category": "general",
        },
    ],
    "overweight": [
        {
            "priority": "medium",
            "message": "⚠️ Tu IMC indica sobrepeso. Considera ajustar tu dieta y aumentar tu actividad física.",
            "category": "nutritional",
        },
        {
            "priority": "medium",
            "message": "📋 Un déficit calórico moderado de 300 kcal puede ayudarte a alcanzar tu peso ideal.",
            "category": "nutritional",
        },
    ],
    "obese_1": [
        {
            "priority": "high",
            "message": "🚨 Alerta: Tu IMC indica obesidad grado I. Se recomienda consulta con especialista.",
            "category": "medical",
        },
        {
            "priority": "high",
            "message": "🏥 Intervention nutricional supervisada y aumento progresivo de actividad física.",
            "category": "nutritional",
        },
    ],
    "obese_2_3": [
        {
            "priority": "critical",
            "message": "🚨 Alerta Clínica: Tu IMC indica obesidad severa. Se requiere intervención médica urgente.",
            "category": "medical",
        },
        {
            "priority": "high",
            "message": "🏥 Control médico continuo, plan nutricional supervisado y actividad física progresiva.",
            "category": "medical",
        },
        {
            "priority": "high",
            "message": "⚠️ Consulta con endocrinólogo y nutricionista para tratamiento integral.",
            "category": "medical",
        },
    ],
}

# ──────────────────────────────────────────────
# Alertas por enfermedades crónicas
# ──────────────────────────────────────────────

DISEASE_ALERTS = {
    "diabetes": {
        "priority": "high",
        "message": "🚨 Alerta Clínica: Plan de comidas bajo en carbohidratos recomendado debido a la Diabetes. Control de glucosa regular.",
        "category": "chronic_disease",
    },
    "hipertensión": {
        "priority": "high",
        "message": "🚨 Alerta Clínica: Evita el exceso de sodio y mantén chequeos de presión arterial por tu Hipertensión.",
        "category": "chronic_disease",
    },
    "hipertension": {
        "priority": "high",
        "message": "🚨 Alerta Clínica: Evita el exceso de sodio y mantén chequeos de presión arterial por tu Hipertensión.",
        "category": "chronic_disease",
    },
    "colesterol": {
        "priority": "high",
        "message": "🚨 Alerta Clínica: Reduce el consumo de grasas saturadas y aumenta la fibra dietary por tu Colesterol alto.",
        "category": "chronic_disease",
    },
}

GENERIC_DISEASE_ALERT = {
    "priority": "high",
    "message": "🚨 Alerta Clínica: Sigue las indicaciones médicas para el manejo de: {disease}.",
    "category": "chronic_disease",
}

# ──────────────────────────────────────────────
# Alertas por estilo de vida (condicionales)
# ──────────────────────────────────────────────

LIFESTYLE_ALERTS = [
    {
        "condition": lambda p: p.get("smokes", False),
        "alert": {
            "priority": "high",
            "message": "🚬 Fumar aumenta significativamente tu riesgo cardiovascular y complicaciones de salud.",
            "category": "lifestyle",
        },
    },
    {
        "condition": lambda p: p.get("sleep_hours", 7) < 6,
        "alert": {
            "priority": "medium",
            "message": "😴 Duermes menos de 6 horas. La falta de sueño afecta tu recuperación, metabolismo y salud general.",
            "category": "lifestyle",
        },
    },
    {
        "condition": lambda p: p.get("sleep_hours", 7) > 9,
        "alert": {
            "priority": "low",
            "message": "ℹ️ Dormir más de 9 horas de forma regular puede estar asociado con otros factores de salud. Considera consultarlo.",
            "category": "lifestyle",
        },
    },
    {
        "condition": lambda p: p.get("activity_level", "moderate") in ["sedentary", "none", "sedentario"],
        "alert": {
            "priority": "medium",
            "message": "🚶 Tu nivel de actividad es muy bajo. Caminar 30 minutos al día puede mejorar significativamente tu salud.",
            "category": "lifestyle",
        },
    },
]

# ──────────────────────────────────────────────
# Alertas por factores genéticos
# ──────────────────────────────────────────────

GENETIC_ALERT = {
    "priority": "medium",
    "message": "🧬 Tienes factores de riesgo genético. Se recomiendan chequeos preventivos regulares y seguimiento médico.",
    "category": "genetic",
}


# ──────────────────────────────────────────────
# Alertas por conflictos objetivo-BMI
# ──────────────────────────────────────────────

GOAL_CONFLICT_ALERTS = {
    "weight_loss_blocked_underweight": {
        "priority": "high",
        "message": "⛔ Tu objetivo de pérdida de peso fue bloqueado: tu peso actual es insuficiente. Priorizamos la ganancia de peso saludable.",
        "category": "goal_conflict",
    },
    "muscle_gain_blocked_obese": {
        "priority": "medium",
        "message": "ℹ️ Priorizamos la pérdida de peso sobre la ganancia muscular debido a tu IMC elevado.",
        "category": "goal_conflict",
    },
}


def generate_alerts(
    bmi_category: str,
    profile: dict,
    chronic_diseases: list,
    genetic_risk_factors: list,
    goal_conflicts: list = None,
    severity: str = None,
) -> list:
    """
    Genera la lista completa de alertas clínicas.

    Cuando severity='critical' y ninguna alerta tiene prioridad 'critical',
    promueve la primera alerta 'high' a 'critical' para mantener consistencia.

    Args:
        bmi_category: categoría BMI del paciente
        profile: dict completo del perfil (smokes, sleep_hours, activity_level, etc.)
        chronic_diseases: lista de enfermedades crónicas
        genetic_risk_factors: lista de factores de riesgo genético
        goal_conflicts: lista de strings de conflictos objetivo-BMI
        severity: severidad compuesta (low/medium/high/critical)

    Returns:
        lista de dicts {priority, message, category}
    """
    alerts = []

    # 1. Alertas base por BMI
    bmi_alerts = BMI_ALERTS.get(bmi_category, [])
    alerts.extend(bmi_alerts)

    # 2. Alertas por conflictos de objetivo
    if goal_conflicts:
        for conflict_key in goal_conflicts:
            if conflict_key in GOAL_CONFLICT_ALERTS:
                alerts.append(GOAL_CONFLICT_ALERTS[conflict_key])

    # 3. Alertas por enfermedades crónicas
    for disease in (chronic_diseases or []):
        disease_lower = disease.lower()
        matched = False
        for key, alert_config in DISEASE_ALERTS.items():
            if key in disease_lower:
                alerts.append(dict(alert_config))
                matched = True
                break
        if not matched:
            alerts.append({
                "priority": GENERIC_DISEASE_ALERT["priority"],
                "message": GENERIC_DISEASE_ALERT["message"].format(disease=disease),
                "category": GENERIC_DISEASE_ALERT["category"],
            })

    # 4. Alertas por factores genéticos
    if len(genetic_risk_factors or []) > 0:
        alerts.append(dict(GENETIC_ALERT))

    # 5. Alertas por estilo de vida
    for rule in LIFESTYLE_ALERTS:
        if rule["condition"](profile):
            alerts.append(dict(rule["alert"]))

    # 6. Si severity=critical y no hay alerta 'critical', promover la primera 'high'
    if severity == "critical":
        has_critical = any(a.get("priority") == "critical" for a in alerts)
        if not has_critical:
            for alert in alerts:
                if alert.get("priority") == "high":
                    alert["priority"] = "critical"
                    break

    return alerts
