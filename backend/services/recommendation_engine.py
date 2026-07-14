"""
RecommendationEngine — Orquestador del Motor de Interpretación Clínica.

Coordina los módulos de reglas y construye la respuesta final
compatible con el frontend existente.

Uso:
    engine = RecommendationEngine()
    result = engine.analyze(
        age=21, gender="male", weight_kg=38, height_cm=169,
        activity_level="sedentary", sleep_hours=5, smokes=False,
        chronic_diseases=[], genetic_risk_factors=[],
        health_goals=["weight_loss"],
        bmi=13.3, bmi_category="severely_underweight",
        bmr=1500.0, tdee=1800.0
    )
"""

from services.rules.bmi_rules import (
    classify_bmi,
    get_bmi_info,
    compute_composite_severity,
)
from services.rules.health_score import calculate_health_score
from services.rules.alert_rules import generate_alerts
from services.rules.nutrition_rules import calculate_nutrition
from services.rules.exercise_rules import calculate_exercise
from services.rules.prediction_rules import generate_predictions


# ──────────────────────────────────────────────
# Validación de objetivos por categoría BMI
# ──────────────────────────────────────────────

GOAL_VALIDATORS = [
    {
        "description": "Bloquear weight_loss y forzar muscle_gain en desnutrición severa",
        "condition": lambda goals, cat: cat == "severely_underweight",
        "remove_goals": ["weight_loss"],
        "add_goals": ["muscle_gain"],
        "conflict_key": "weight_loss_blocked_underweight",
    },
    {
        "description": "Bloquear weight_loss en bajo peso",
        "condition": lambda goals, cat: cat == "underweight",
        "remove_goals": ["weight_loss"],
        "add_goals": ["muscle_gain"],
        "conflict_key": "weight_loss_blocked_underweight",
    },
    {
        "description": "Bloquear muscle_gain en obesidad I",
        "condition": lambda goals, cat: cat == "obese_1",
        "remove_goals": ["muscle_gain"],
        "add_goals": ["weight_loss"],
        "conflict_key": "muscle_gain_blocked_obese",
    },
    {
        "description": "Bloquear muscle_gain en obesidad II/III",
        "condition": lambda goals, cat: cat == "obese_2_3",
        "remove_goals": ["muscle_gain"],
        "add_goals": ["weight_loss"],
        "conflict_key": "muscle_gain_blocked_obese",
    },
]

# ──────────────────────────────────────────────
# Descripciones de severidad para clinical_summary
# ──────────────────────────────────────────────

SEVERITY_DESCRIPTIONS = {
    "critical": {
        "title": "Estado Crítico — Intervención Médica Urgente",
        "description": (
            "Tu perfil clínico indica una situación de alto riesgo que requiere atención médica "
            "inmediata. No sigas recomendaciones genéricas. Consulta a un profesional de salud "
            "lo antes posible para recibir un plan de tratamiento personalizado."
        ),
    },
    "high": {
        "title": "Riesgo Alto — Consulta Médica Recomendada",
        "description": (
            "Tu perfil presenta factores de riesgo significativos. Se recomienda consultar con "
            "un médico o especialista para recibir orientación clínica personalizada."
        ),
    },
    "medium": {
        "title": "Riesgo Moderado — Mejora de Hábitos Necesaria",
        "description": (
            "Tu perfil indica áreas de mejora. Con ajustes a tu dieta, actividad física y "
            "hábitos de vida puedes mejorar significativamente tu estado de salud."
        ),
    },
    "low": {
        "title": "Buen Estado de Salud — Mantén tus Hábitos",
        "description": (
            "Tu perfil indica un estado de salud saludable. Mantén tus hábitos actuales "
            "y continúa con chequeos preventivos regulares."
        ),
    },
}


class RecommendationEngine:
    """
    Orquestador del Motor de Interpretación Clínica.

    Coordina módulos de reglas independientes para generar:
    - Health Score (puntaje de salud)
    - Alertas clínicas
    - Objetivos semanales
    - Plan nutricional
    - Plan de ejercicio
    - Predicciones de peso
    - Resumen clínico (clinical_summary)

    Preparado para recibir resultados de modelos ML en futuras fases.
    """

    def analyze(
        self,
        age: int,
        gender: str,
        weight_kg: float,
        height_cm: float,
        activity_level: str,
        sleep_hours: int,
        smokes: bool,
        chronic_diseases: list,
        genetic_risk_factors: list,
        health_goals: list,
        bmi: float,
        bmi_category: str,
        bmr: float,
        tdee: float,
        ml_prediction: dict = None,
    ) -> dict:
        """
        Ejecuta el análisis completo del motor de recomendaciones.

        Args:
            age: Edad del paciente
            gender: Género ('male' / 'female')
            weight_kg: Peso en kg
            height_cm: Altura en cm
            activity_level: Nivel de actividad (sedentary/light/moderate/active/very_active)
            sleep_hours: Horas de sueño
            smokes: Si fuma
            chronic_diseases: Lista de enfermedades crónicas
            genetic_risk_factors: Lista de factores de riesgo genético
            health_goals: Lista de objetivos del usuario
            bmi: IMC calculado
            bmi_category: Categoría BMI calculada
            bmr: Tasa metabólica basal
            tdee: Gasto energético total diario
            ml_prediction: Resultado del modelo ML (opcional)
                {predicted_class, probabilities, confidence, model_used}

        Returns:
            dict compatible con el frontend, incluyendo clinical_summary
        """
        # ── Perfil del paciente como dict para módulos de reglas ──
        profile = {
            "age": age,
            "gender": gender,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "activity_level": activity_level,
            "sleep_hours": sleep_hours,
            "smokes": smokes,
            "chronic_diseases": chronic_diseases or [],
            "genetic_risk_factors": genetic_risk_factors or [],
        }

        metrics = {
            "bmi": bmi,
            "bmi_category": bmi_category,
            "bmr": bmr,
            "tdee": tdee,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "age": age,
        }

        # ── 1. Validar y ajustar objetivos ──
        adjusted_goals, goal_conflicts = self._validate_goals(
            health_goals, bmi_category
        )

        # ── 2. Calcular severidad compuesta ──
        severity = compute_composite_severity(
            bmi_category=bmi_category,
            chronic_diseases=chronic_diseases,
            smokes=smokes,
            activity_level=activity_level,
            sleep_hours=sleep_hours,
        )

        # ── 3. Calcular health score ──
        score_result = calculate_health_score(bmi, profile, severity=severity)

        # ── 4. Generar alertas ──
        alerts = generate_alerts(
            bmi_category=bmi_category,
            profile=profile,
            chronic_diseases=chronic_diseases,
            genetic_risk_factors=genetic_risk_factors,
            goal_conflicts=goal_conflicts,
            severity=severity,
        )

        # ── 5. Generar objetivos semanales ──
        weekly_goals = self._generate_weekly_goals(
            adjusted_goals, bmi_category, metrics
        )

        # ── 6. Calcular plan nutricional ──
        nutrition = calculate_nutrition(
            bmi=bmi,
            bmi_category=bmi_category,
            tdee=tdee,
            weight_kg=weight_kg,
            goals=adjusted_goals,
            chronic_diseases=chronic_diseases,
        )

        # ── 7. Calcular plan de ejercicio ──
        exercise = calculate_exercise(
            activity_level=activity_level,
            bmi_category=bmi_category,
            goals=adjusted_goals,
            age=age,
        )

        # ── 8. Generar predicciones ──
        predictions = generate_predictions(
            weight_kg=weight_kg,
            bmi_category=bmi_category,
            goals=adjusted_goals,
            ml_prediction=ml_prediction,
        )

        # ── 9. Construir clinical_summary ──
        clinical_summary = self._build_clinical_summary(
            severity=severity,
            bmi_category=bmi_category,
            bmi=bmi,
            alerts=alerts,
            score=score_result["score"],
        )

        # ── 10. Construir respuesta compatible con frontend ──
        health_plan = {
            "nutrition": {
                "daily_calories": nutrition["daily_calories"],
                "macronutrients": nutrition["macronutrients"],
                "recommendations": nutrition["recommendations"],
            },
            "exercise": {
                "cardio": exercise["cardio"],
                "strength": exercise["strength"],
                "flexibility": exercise["flexibility"],
            },
        }

        return {
            "health_score": score_result["score"],
            "health_risk": score_result["risk_label"],
            "health_risk_level": score_result["risk_level"],
            "fitness_level": exercise["fitness_level"],
            "alerts": alerts,
            "weekly_goals": weekly_goals,
            "health_plan": health_plan,
            "predictions": {
                "predictions_data": predictions["predictions_data"],
                "model_used": predictions["model_used"],
                "confidence_score": predictions["confidence_score"],
            },
            "clinical_summary": clinical_summary,
            "_debug": {
                "severity": severity,
                "adjusted_goals": adjusted_goals,
                "goal_conflicts": goal_conflicts,
                "applied_penalties": score_result["applied_penalties"],
                "nutrition_calorie_note": nutrition.get("calorie_note", ""),
                "exercise_notes": exercise.get("notes", []),
                "prediction_note": predictions.get("note", ""),
            },
        }

    def _validate_goals(self, goals: list, bmi_category: str) -> tuple:
        """
        Valida y ajusta los objetivos según la categoría BMI.

        Returns:
            (adjusted_goals, conflict_keys)
        """
        adjusted = list(goals or [])
        conflicts = []

        for validator in GOAL_VALIDATORS:
            if validator["condition"](adjusted, bmi_category):
                for g in validator["remove_goals"]:
                    if g in adjusted:
                        adjusted.remove(g)
                for g in validator["add_goals"]:
                    if g not in adjusted:
                        adjusted.append(g)
                if validator["conflict_key"]:
                    conflicts.append(validator["conflict_key"])

        if not adjusted:
            adjusted = ["general_wellness"]

        return adjusted, conflicts

    def _generate_weekly_goals(
        self, goals: list, bmi_category: str, metrics: dict
    ) -> list:
        """
        Genera objetivos semanales descriptivos y dinámicos.
        """
        weekly = []

        # Objetivos derivados de BMI
        bmi_info = get_bmi_info(bmi_category)
        if bmi_category in ["severely_underweight", "underweight"]:
            target_min = round(metrics["weight_kg"] + 2, 1)
            weekly.append(
                f"Aumentar peso progresivamente hacia {target_min}+ kg de forma saludable"
            )
            weekly.append("Consulta con nutricionista para plan de alimentación personalizado")
            if bmi_category == "severely_underweight":
                weekly.append("Seguimiento médico semanal hasta estabilizar peso")

        elif bmi_category in ["overweight", "obese_1", "obese_2_3"]:
            target_max = round(metrics["weight_kg"] - 2, 1)
            weekly.append(
                f"Reducir peso progresivamente hacia {target_max} kg de forma sostenible"
            )
            if bmi_category in ["obese_1", "obese_2_3"]:
                weekly.append("Consulta con especialista para supervisión del proceso")

        elif bmi_category == "normal":
            weekly.append("Mantener peso actual con hábitos saludables")

        # Objetivos derivados de goals del usuario
        goal_descriptions = {
            "weight_loss": "Seguir plan alimentario con déficit calórico controlado",
            "muscle_gain": "Entrenamiento de resistance 3-4 veces por semana",
            "better_sleep": "Establecer rutina de sueño: 7-8 horas por noche",
            "stress_reduction": "Practicar técnicas de relajación 10 min al día",
            "energy_boost": "Realizar ejercicio moderado 30 min diarios",
            "general_wellness": "Mantener hidratación adecuada (2+ litros/día)",
        }
        for goal in goals:
            desc = goal_descriptions.get(goal)
            if desc:
                weekly.append(desc)

        if not weekly:
            weekly = [
                "Mantener una dieta balanceada",
                "Ejercicio 3 veces por semana",
                "Dormir al menos 7 horas",
            ]

        return weekly

    def _build_clinical_summary(
        self, severity: str, bmi_category: str, bmi: float, alerts: list, score: int
    ) -> dict:
        """
        Construye el campo clinical_summary con severidad, título y descripción.
        Este campo es complementario y no reemplaza nada existente.
        """
        desc = SEVERITY_DESCRIPTIONS.get(severity, SEVERITY_DESCRIPTIONS["low"])

        bmi_info = get_bmi_info(bmi_category)
        high_priority_alerts = [a for a in alerts if a.get("priority") == "high"]

        return {
            "severity": severity,
            "title": desc["title"],
            "description": desc["description"],
            "bmi_label": bmi_info.get("label", ""),
            "bmi_description": bmi_info.get("description", ""),
            "health_score": score,
            "critical_alerts_count": len(high_priority_alerts),
            "requires_medical_attention": severity in ["critical", "high"],
        }
