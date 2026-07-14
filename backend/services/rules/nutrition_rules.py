"""
Nutrition Rules — Planes nutricionales dinámicos basados en categoría BMI, objetivos y perfil.

Estrategias nutricionales por categoría BMI con modificadores por objetivo.
"""


# ──────────────────────────────────────────────
# Estrategias base por categoría BMI
# ──────────────────────────────────────────────

NUTRITION_STRATEGIES = {
    "severely_underweight": {
        "calorie_adjustment": 600,
        "protein_per_kg": 2.0,
        "macro_ratios": {"protein": 0.25, "carbs": 0.50, "fats": 0.25},
        "recommendations": [
            "Consulta con nutricionista para un plan de alimentación personalizado.",
            "Aumenta tu ingesta calórica de forma gradual y supervisada.",
            "Incluye alimentos densos en nutrientes: frutos secos, aguacate, huevos, legumbres.",
            "Realiza 5-6 comidas al día para facilitar la ingesta calórica.",
            "Incluye batidos nutritivos entre comidas para aumentar calorías sin saturación.",
        ],
        "calorie_note": "Superávit calórico para recuperación de peso supervisada.",
    },
    "underweight": {
        "calorie_adjustment": 400,
        "protein_per_kg": 1.8,
        "macro_ratios": {"protein": 0.25, "carbs": 0.50, "fats": 0.25},
        "recommendations": [
            "Aumenta la ingesta calórica con alimentos nutritivos y naturales.",
            "Distribuye tus comidas en 5 porciones al día.",
            "Prioriza fuentes de proteína de alta calidad: pollo, pescado, huevos, lácteos.",
            "Incluye carbohidratos complejos: arroz, avena, papa, pan integral.",
            "Evita las dietas restrictivas. Tu objetivo es alcanzar un peso saludable.",
        ],
        "calorie_note": "Superávit calórico moderado para alcanzar peso saludable.",
    },
    "normal": {
        "calorie_adjustment": 0,
        "protein_per_kg": 1.4,
        "macro_ratios": {"protein": 0.30, "carbs": 0.40, "fats": 0.30},
        "recommendations": [
            "Mantén una dieta variada y equilibrada.",
            "Prioriza alimentos no procesados y frescos.",
            "Mantén una ingesta adecuada de proteínas para preservar masa muscular.",
            "Aumenta el consumo de fibra: verduras, frutas, legumbres.",
            "Distribuye tus comidas de forma regular a lo largo del día.",
        ],
        "calorie_note": "Mantener ingesta actual para peso estable.",
    },
    "overweight": {
        "calorie_adjustment": -300,
        "protein_per_kg": 1.6,
        "macro_ratios": {"protein": 0.30, "carbs": 0.35, "fats": 0.35},
        "recommendations": [
            "Implementa un déficit calórico moderado de 300 kcal diarias.",
            "Prioriza alimentos con alto contenido proteico para mantener masa muscular.",
            "Reduce carbohidratos refinados: azúcar, harinas blancas, bebidas azucaradas.",
            "Aumenta el consumo de verduras y fibra para mejorar la saciedad.",
            "Controla las porciones y evita el exceso de grasas saturadas.",
        ],
        "calorie_note": "Déficit calórico moderado para pérdida de peso sostenible.",
    },
    "obese_1": {
        "calorie_adjustment": -500,
        "protein_per_kg": 1.6,
        "macro_ratios": {"protein": 0.30, "carbs": 0.35, "fats": 0.35},
        "recommendations": [
            "Déficit calórico de 500 kcal bajo supervisión médica/nutricional.",
            "Prioriza proteínas magras para preservar masa muscular durante la pérdida de peso.",
            "Elimina ultraprocesados, azúcares añadidos y grasas trans.",
            "Aumenta el consumo de verduras no almidonadas.",
            "Lleva un registro alimentario semanal para seguimiento.",
            "Consulta con nutricionista para plan personalizado.",
        ],
        "calorie_note": "Déficit calórico controlado para pérdida de peso progresiva.",
    },
    "obese_2_3": {
        "calorie_adjustment": -500,
        "protein_per_kg": 1.6,
        "macro_ratios": {"protein": 0.30, "carbs": 0.35, "fats": 0.35},
        "recommendations": [
            "Plan nutricional supervisado por especialista es obligatorio.",
            "Déficit calórico con seguimiento médico regular.",
            "Enfócate en alimentos integrales y elimina ultraprocesados.",
            "Proteína alta para preservar masa muscular durante la pérdida de peso.",
            "Control de porciones y horarios de comida estrictos.",
            "Seguimiento nutricional quincenal para ajustes.",
        ],
        "calorie_note": "Plan nutricional supervisado por profesional de salud.",
    },
}

# ──────────────────────────────────────────────
# Modificadores de objetivo
# ──────────────────────────────────────────────

GOAL_NUTRITION_MODIFIERS = {
    "weight_loss": {
        "calorie_adjustment": -200,
        "macro_adjustments": {"protein": 0.05, "carbs": -0.05, "fats": 0.0},
        "extra_recommendations": [
            "Mantén un déficit calórico sostenible para pérdida progresiva.",
            "Pesa los alimentos para controlar porciones con precisión.",
        ],
    },
    "muscle_gain": {
        "calorie_adjustment": 200,
        "macro_adjustments": {"protein": 0.05, "carbs": 0.0, "fats": -0.05},
        "extra_recommendations": [
            "Aumenta la ingesta proteíca a 1.6-2.0 g/kg de peso corporal.",
            "Distribuye la proteína en cada comida del día.",
        ],
    },
    "better_sleep": {
        "calorie_adjustment": 0,
        "macro_adjustments": {},
        "extra_recommendations": [
            "Evita cafeína después de las 6 PM.",
            "Incluye alimentos ricos en triptófano: leche, plátano, avena.",
        ],
    },
    "stress_reduction": {
        "calorie_adjustment": 0,
        "macro_adjustments": {},
        "extra_recommendations": [
            "Incluye alimentos ricos en omega-3: pescado, nueces, semillas de chía.",
            "Mantén horarios regulares de comida para reducir el estrés metabólico.",
        ],
    },
    "energy_boost": {
        "calorie_adjustment": 100,
        "macro_adjustments": {"protein": 0.0, "carbs": 0.05, "fats": -0.05},
        "extra_recommendations": [
            "Prioriza carbohidratos de bajo índice glucémico para energía sostenida.",
            "Mantén buena hidratación durante el día.",
        ],
    },
    "general_wellness": {
        "calorie_adjustment": 0,
        "macro_adjustments": {},
        "extra_recommendations": [
            "Bebe al menos 2 litros de agua al día.",
            "Incluye una variedad de colores en tu dieta (frutas y verduras).",
        ],
    },
}

# ──────────────────────────────────────────────
# Ajustes por enfermedades crónicas
# ──────────────────────────────────────────────

DISEASE_NUTRITION_MODIFIERS = {
    "diabetes": {
        "macro_adjustments": {"protein": 0.0, "carbs": -0.10, "fats": 0.10},
        "extra_recommendations": [
            "Controla la ingesta de carbohidratos simples. Prefiere carbohidratos complejos.",
            "Monitorea tus niveles de glucosa antes y después de las comidas principales.",
            "Evita bebidas azucaradas y productos con azúcar añadida.",
        ],
    },
    "hipertensión": {
        "extra_recommendations": [
            "Limita el consumo de sodio a menos de 2,300 mg diarios.",
            "Evita alimentos procesados altos en sodio: embutidos, enlatados, snacks.",
            "Aumenta el consumo de potasio: plátano, espinaca, papa.",
        ],
    },
    "hipertension": {
        "extra_recommendations": [
            "Limita el consumo de sodio a menos de 2,300 mg diarios.",
            "Evita alimentos procesados altos en sodio: embutidos, enlatados, snacks.",
            "Aumenta el consumo de potasio: plátano, espinaca, papa.",
        ],
    },
    "colesterol": {
        "macro_adjustments": {"protein": 0.0, "carbs": 0.0, "fats": -0.05},
        "extra_recommendations": [
            "Reduce grasas saturadas: limita carnes rojas, mantequilla, queso.",
            "Aumenta fibra soluble: avena, manzana, legumbres, semillas de linaza.",
            "Incluye grasas saludables: aceite de oliva, aguacate, frutos secos.",
        ],
    },
}


def calculate_nutrition(
    bmi: float,
    bmi_category: str,
    tdee: float,
    weight_kg: float,
    goals: list,
    chronic_diseases: list = None,
) -> dict:
    """
    Genera el plan nutricional completo.

    Args:
        bmi: IMC del paciente
        bmi_category: categoría BMI
        tdee: gasto energético total diario
        weight_kg: peso actual en kg
        goals: lista de objetivos del paciente
        chronic_diseases: lista de enfermedades crónicas

    Returns:
        dict con daily_calories, macronutrients, recommendations, calorie_note
    """
    strategy = NUTRITION_STRATEGIES.get(bmi_category, NUTRITION_STRATEGIES["normal"])

    calorie_adj = strategy["calorie_adjustment"]
    protein_ratio = strategy["macro_ratios"]["protein"]
    carbs_ratio = strategy["macro_ratios"]["carbs"]
    fats_ratio = strategy["macro_ratios"]["fats"]
    protein_per_kg = strategy["protein_per_kg"]

    recommendations = list(strategy["recommendations"])

    # Aplicar modificadores por objetivo
    for goal in goals:
        modifier = GOAL_NUTRITION_MODIFIERS.get(goal)
        if modifier:
            calorie_adj += modifier["calorie_adjustment"]
            adj = modifier["macro_adjustments"]
            protein_ratio += adj.get("protein", 0)
            carbs_ratio += adj.get("carbs", 0)
            fats_ratio += adj.get("fats", 0)
            recommendations.extend(modifier.get("extra_recommendations", []))

    # Aplicar modificadores por enfermedades crónicas
    for disease in (chronic_diseases or []):
        disease_lower = disease.lower()
        for key, modifier in DISEASE_NUTRITION_MODIFIERS.items():
            if key in disease_lower:
                adj = modifier.get("macro_adjustments", {})
                protein_ratio += adj.get("protein", 0)
                carbs_ratio += adj.get("carbs", 0)
                fats_ratio += adj.get("fats", 0)
                recommendations.extend(modifier.get("extra_recommendations", []))
                break

    # Normalizar ratios para que sumen 1.0
    total = protein_ratio + carbs_ratio + fats_ratio
    if total > 0:
        protein_ratio /= total
        carbs_ratio /= total
        fats_ratio /= total

    # Calcular calorías finales
    daily_calories = int(tdee + calorie_adj)
    daily_calories = max(1200, min(5000, daily_calories))

    # Calcular macronutrientes en gramos
    protein_g = int((daily_calories * protein_ratio) / 4)
    carbs_g = int((daily_calories * carbs_ratio) / 4)
    fats_g = int((daily_calories * fats_ratio) / 9)

    # Ajuste final para desnutrición: asegurar mínimo proteína y cap máximo
    min_protein = int(weight_kg * protein_per_kg)
    max_protein = int(weight_kg * 3.0)
    protein_g = max(min_protein, min(max_protein, protein_g))

    return {
        "daily_calories": daily_calories,
        "macronutrients": {
            "protein": protein_g,
            "carbs": carbs_g,
            "fats": fats_g,
        },
        "recommendations": recommendations,
        "calorie_note": strategy.get("calorie_note", ""),
    }
