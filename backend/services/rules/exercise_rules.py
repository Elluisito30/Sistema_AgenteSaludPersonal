"""
Exercise Rules — Planes de ejercicio personalizados por categoría BMI y perfil del paciente.

Estrategias de ejercicio con modificadores por objetivo y condición.
"""


# ──────────────────────────────────────────────
# Planes base por nivel de actividad
# ──────────────────────────────────────────────

ACTIVITY_BASE_PLANS = {
    "sedentary": {
        "cardio": "Caminata ligera 20 min, 3 días/semana",
        "strength": "Ejercicios de resistance con peso corporal 15 min, 2 días/semana",
        "flexibility": "Estiramientos básicos 10 min/día",
        "fitness_level": "beginner",
    },
    "light": {
        "cardio": "Caminata o bicicleta 30 min, 3 días/semana",
        "strength": "Resistance moderada 20 min, 2 días/semana",
        "flexibility": "Estiramientos 10 min/día",
        "fitness_level": "beginner",
    },
    "moderate": {
        "cardio": "Cardio moderado 40 min, 4 días/semana",
        "strength": "Resistance 25 min, 3 días/semana",
        "flexibility": "Yoga o estiramientos 10 min/día",
        "fitness_level": "intermediate",
    },
    "active": {
        "cardio": "Cardio intenso 50 min, 5 días/semana",
        "strength": "Resistance progresiva 30 min, 3 días/semana",
        "flexibility": "Movilidad 15 min/día",
        "fitness_level": "intermediate",
    },
    "very_active": {
        "cardio": "Cardio intenso 60 min, 6 días/semana",
        "strength": "Resistance avanzada 35 min, 4 días/semana",
        "flexibility": "Movilidad y flexibilidad 15 min/día",
        "fitness_level": "advanced",
    },
}

# ──────────────────────────────────────────────
# Modificadores por categoría BMI
# ──────────────────────────────────────────────

BMI_EXERCISE_MODIFIERS = {
    "severely_underweight": {
        "cardio_override": "Caminata suave 15 min, 2 días/semana. Evitar cardio intenso.",
        "strength_override": "Ejercicios de resistance ligeros con peso corporal 15 min, 2 días/semana",
        "flexibility_override": "Estiramientos suaves 10 min/día. Evitar esfuerzo excesivo.",
        "fitness_level_override": "beginner",
        "notes": "Enfocarse en ganancia muscular progresiva. Evitar ejercicio cardiovascular intenso que consuma muchas calorías.",
    },
    "underweight": {
        "cardio_override": "Caminata moderada 20 min, 3 días/semana",
        "strength_override": "Resistance ligera a moderada 20 min, 2-3 días/semana",
        "flexibility_override": "Estiramientos 10 min/día",
        "fitness_level_override": "beginner",
        "notes": "Priorizar ejercicios de resistance para ganar masa muscular. Cardio moderado no más de 3 días.",
    },
    "normal": {
        "notes": "Plan de ejercicio equilibrado. Mantener buena combinación de cardio, fuerza y flexibilidad.",
    },
    "overweight": {
        "cardio_adjustment": "+1 sesión de cardio semanal para aumentar gasto calórico",
        "strength_adjustment": "Mantener resistance para preservar masa muscular durante la pérdida de peso",
        "notes": "Priorizar consistencia sobre intensidad. Aumentar gradualmente la carga de entrenamiento.",
    },
    "obese_1": {
        "cardio_override": "Caminata o natación 30 min, 4 días/semana (bajo impacto)",
        "strength_override": "Resistance ligera con máquina o peso corporal 20 min, 2-3 días/semana",
        "flexibility_override": "Estiramientos y movilidad 15 min/día",
        "fitness_level_override": "beginner",
        "notes": "Ejercicio de bajo impacto para proteger articulaciones. Progresión gradual. Evitar impacto alto.",
    },
    "obese_2_3": {
        "cardio_override": "Caminata suave 20 min, 3 días/semana o aquatic exercise",
        "strength_override": "Resistance con bandas elásticas o peso corporal 15 min, 2 días/semana",
        "flexibility_override": "Movilidad articular suave 10 min/día",
        "fitness_level_override": "beginner",
        "notes": "Ejercicio supervisado recomendado. Comenzar con sesiones cortas y progresar lentamente. Priorizar adherencia.",
    },
}

# ──────────────────────────────────────────────
# Modificadores por objetivo
# ──────────────────────────────────────────────

GOAL_EXERCISE_MODIFIERS = {
    "weight_loss": {
        "cardio_note": "Aumentar frecuencia cardiovascular para mayor gasto calórico.",
        "strength_note": "Mantener resistance para preservar masa muscular durante la pérdida de peso.",
    },
    "muscle_gain": {
        "strength_note": "Priorizar entrenamiento de resistance con carga progresiva.",
        "cardio_note": "Cardio moderado para salud cardiovascular sin comprometer ganancia muscular.",
    },
    "better_sleep": {
        "cardio_note": "Evitar ejercicio intenso en las 3 horas antes de dormir.",
        "flexibility_note": "Incluir rutinas de relajación y yoga nocturno.",
    },
    "stress_reduction": {
        "cardio_note": "Ejercicio al aire libre, natación o ciclismo para reducir estrés.",
        "flexibility_note": "Incluir yoga o pilates 2-3 veces por semana.",
    },
    "energy_boost": {
        "cardio_note": "Ejercicio matutino para activar el metabolismo del día.",
    },
    "general_wellness": {
        "cardio_note": "Mantener rutina constante de ejercicio variado.",
    },
}


def calculate_exercise(
    activity_level: str,
    bmi_category: str,
    goals: list,
    age: int = 30,
) -> dict:
    """
    Genera el plan de ejercicio personalizado.

    Args:
        activity_level: nivel de actividad del paciente
        bmi_category: categoría BMI
        goals: lista de objetivos
        age: edad del paciente

    Returns:
        dict con cardio, strength, flexibility, fitness_level, notes
    """
    base = ACTIVITY_BASE_PLANS.get(activity_level, ACTIVITY_BASE_PLANS["moderate"])

    cardio = base["cardio"]
    strength = base["strength"]
    flexibility = base["flexibility"]
    fitness_level = base["fitness_level"]
    notes = []

    # Aplicar modificadores BMI
    bmi_mod = BMI_EXERCISE_MODIFIERS.get(bmi_category, {})
    if "cardio_override" in bmi_mod:
        cardio = bmi_mod["cardio_override"]
    if "strength_override" in bmi_mod:
        strength = bmi_mod["strength_override"]
    if "flexibility_override" in bmi_mod:
        flexibility = bmi_mod["flexibility_override"]
    if "fitness_level_override" in bmi_mod:
        fitness_level = bmi_mod["fitness_level_override"]
    if "notes" in bmi_mod:
        notes.append(bmi_mod["notes"])

    # Aplicar modificadores por objetivo
    for goal in goals:
        goal_mod = GOAL_EXERCISE_MODIFIERS.get(goal, {})
        for key in ["cardio_note", "strength_note", "flexibility_note"]:
            if key in goal_mod:
                notes.append(goal_mod[key])

    # Ajuste por edad
    if age >= 65:
        notes.append("Para mayores de 65 años: priorizar ejercicios de bajo impacto y equilibrio.")
        if "low impact" not in cardio.lower() and "suave" not in cardio.lower():
            cardio = cardio.replace("min", "min (bajo impacto)")

    return {
        "cardio": cardio,
        "strength": strength,
        "flexibility": flexibility,
        "fitness_level": fitness_level,
        "notes": notes,
    }
