"""
Report Engine — Motor de Reportes Inteligentes.

Capa de datos centralizada entre endpoints y advanced_reports.py (renderizado).

Responsabilidades:
1. Recopilar datos de múltiples fuentes (respuesta de análisis o DB)
2. Unificar perfil + análisis + ML + XAI + alertas + objetivos + nutrición + ejercicio
3. Organizar por 11 secciones
4. Generar narratives interpretativas (LLM-ready)
5. Entregar un objeto estructurado reutilizable

NO genera PDF, Excel ni Word.
NO accede a BD directamente.
NO modifica servicios existentes.

Uso:
    engine = ReportEngine()
    report = engine.build_from_analysis_response(analysis_response, profile, history)
    report = engine.build_from_db(profile, analysis, predictions, history, language="es")
"""

from datetime import datetime

from services.reports.styles import get_bmi_category_label, get_translations


# ──────────────────────────────────────────────
# Constantes para narratives
# ──────────────────────────────────────────────

BMI_CATEGORY_DESCRIPTIONS = {
    "es": {
        "severely_underweight": (
            "IMC por debajo de 16, indicando desnutrición severa que requiere "
            "intervención médica inmediata."
        ),
        "underweight": (
            "IMC entre 16 y 18.5, indicando peso insuficiente. "
            "Se recomienda valoración nutricional."
        ),
        "normal": (
            "IMC dentro del rango saludable (18.5-25). Mantener hábitos actuales."
        ),
        "overweight": (
            "IMC entre 25 y 30, indicando sobrepeso. "
            "Se sugiere ajuste en dieta y actividad física."
        ),
        "obese_1": (
            "IMC entre 30 y 35, indicando obesidad grado I. "
            "Se requiere intervención nutricional y control médico."
        ),
        "obese_2_3": (
            "IMC mayor a 35, indicando obesidad severa. "
            "Intervención médica urgente necesaria."
        ),
    },
    "en": {
        "severely_underweight": (
            "BMI below 16, indicating severe undernutrition that requires "
            "immediate medical intervention."
        ),
        "underweight": (
            "BMI between 16 and 18.5, indicating insufficient weight. "
            "Nutritional assessment is recommended."
        ),
        "normal": (
            "BMI within the healthy range (18.5-25). Maintain current habits."
        ),
        "overweight": (
            "BMI between 25 and 30, indicating overweight. "
            "Diet and physical activity adjustments are suggested."
        ),
        "obese_1": (
            "BMI between 30 and 35, indicating obesity class I. "
            "Nutritional intervention and medical follow-up are required."
        ),
        "obese_2_3": (
            "BMI above 35, indicating severe obesity. "
            "Urgent medical intervention is necessary."
        ),
    },
}

SEVERITY_DESCRIPTIONS = {
    "es": {
        "critical": (
            "El estado actual representa un riesgo elevado para la salud. "
            "Se recomienda atención médica supervisada de forma prioritaria."
        ),
        "high": (
            "El nivel de riesgo es alto. Es importante tomar acciones "
            "correctivas con acompañamiento profesional."
        ),
        "medium": (
            "El riesgo es moderado. Con cambios graduales en los hábitos "
            "se puede mejorar significativamente la situación actual."
        ),
        "low": (
            "El nivel de riesgo es bajo. Se recomienda mantener los "
            "hábitos actuales y realizar seguimiento periódico."
        ),
        "optimal": (
            "El estado de salud es óptimo. Se recomienda mantener "
            "los hábitos actuales para conservar este nivel."
        ),
    },
    "en": {
        "critical": (
            "The current status represents an elevated health risk. "
            "Supervised medical attention is recommended as a priority."
        ),
        "high": (
            "The risk level is high. Corrective actions with "
            "professional support are important."
        ),
        "medium": (
            "The risk is moderate. Gradual habit changes can "
            "significantly improve the current situation."
        ),
        "low": (
            "The risk level is low. Maintaining current habits "
            "and periodic follow-up are recommended."
        ),
        "optimal": (
            "Health status is optimal. Maintaining current habits "
            "is recommended to preserve this level."
        ),
    },
}

ACTIVITY_LABELS = {
    "sedentary": {"es": "Sedentario", "en": "Sedentary"},
    "light": {"es": "Ligero", "en": "Light"},
    "moderate": {"es": "Moderado", "en": "Moderate"},
    "active": {"es": "Activo", "en": "Active"},
    "very_active": {"es": "Muy Activo", "en": "Very Active"},
}

GENDER_LABELS = {
    "male": {"es": "Masculino", "en": "Male"},
    "female": {"es": "Femenino", "en": "Female"},
}


def _lang(language):
    return language if language in ("es", "en") else "es"


def _label_map(mapping, key, language="es"):
    entry = mapping.get(key)
    if not entry:
        return key
    if isinstance(entry, dict):
        return entry.get(_lang(language), entry.get("es", key))
    return entry


# ──────────────────────────────────────────────
# ReportEngine
# ──────────────────────────────────────────────

class ReportEngine:
    """
    Motor de Reportes — Capa de datos entre endpoints y renderizado.

    Construye un objeto unificado a partir de:
    - Respuesta de /api/analyze (datos en tiempo real con ML + XAI)
    - Datos de BD (reportes históricos, puede faltar ML + XAI)

    El objeto resultante contiene 11 secciones:
      1. profile       — Datos demográficos y clínicos del paciente
      2. analysis      — Métricas clínicas (score, BMI, BMR, TDEE, riesgo)
      3. ml_prediction — Predicción del modelo XGBoost
      4. xai           — Explicación interpretable del modelo
      5. alerts        — Alertas clínicas priorizadas
      6. goals         — Objetivos semanales
      7. nutrition     — Plan nutricional
      8. exercise      — Plan de ejercicio
      9. predictions   — Proyecciones de peso
     10. history       — Histórico de análisis
     11. narratives    — Textos interpretativos (LLM-ready)
    """

    def build_from_analysis_response(
        self, analysis_response, profile, history=None, language="es"
    ):
        """
        Construye ReportData desde la respuesta completa de /api/analyze.

        Incluye ML + XAI (datos disponibles solo en tiempo real).
        """
        ar = analysis_response or {}
        health_plan = ar.get("health_plan") or {}
        lang = _lang(language)

        return {
            "generated_at": datetime.now().isoformat(),
            "source": "live_analysis",
            "language": lang,
            "profile": self._build_profile_section(profile, lang),
            "analysis": self._build_analysis_section(ar, lang),
            "ml_prediction": self._build_ml_section(ar.get("ml_prediction")),
            "xai": self._build_xai_section(ar.get("xai")),
            "alerts": self._build_alerts_section(ar.get("alerts")),
            "goals": self._build_goals_section(ar.get("weekly_goals"), lang),
            "nutrition": self._build_nutrition_section(health_plan),
            "exercise": self._build_exercise_section(health_plan),
            "predictions": self._build_predictions_section(
                ar.get("predictions"), ar
            ),
            "history": self._build_history_section(history),
            "narratives": self._build_narratives(
                profile=profile,
                analysis=ar,
                ml_prediction=ar.get("ml_prediction"),
                xai=ar.get("xai"),
                alerts=ar.get("alerts"),
                goals=ar.get("weekly_goals"),
                clinical_summary=ar.get("clinical_summary"),
                health_plan=health_plan,
                predictions=ar.get("predictions"),
                language=lang,
            ),
        }

    def build_from_db(
        self, profile, analysis, predictions=None, history=None, language="es"
    ):
        """
        Construye ReportData desde datos de BD (reportes históricos).

        Puede no incluir ml_prediction ni xai si no están almacenados.
        Reconstruye ml_prediction parcialmente desde health_predictions si existe.
        """
        analysis = analysis or {}
        health_plan = analysis.get("health_plan") or {}
        if isinstance(health_plan, str):
            import json
            try:
                health_plan = json.loads(health_plan)
            except (json.JSONDecodeError, TypeError):
                health_plan = {}

        lang = _lang(language)
        ml_from_db = self._reconstruct_ml_from_predictions(predictions)

        return {
            "generated_at": datetime.now().isoformat(),
            "source": "database",
            "language": lang,
            "profile": self._build_profile_section(profile, lang),
            "analysis": self._build_analysis_section(analysis, lang),
            "ml_prediction": self._build_ml_section(ml_from_db),
            "xai": self._build_xai_section(None),
            "alerts": self._build_alerts_section(analysis.get("alerts")),
            "goals": self._build_goals_section(analysis.get("weekly_goals"), lang),
            "nutrition": self._build_nutrition_section(health_plan),
            "exercise": self._build_exercise_section(health_plan),
            "predictions": self._build_predictions_section(
                self._extract_predictions_from_db(predictions), analysis
            ),
            "history": self._build_history_section(history),
            "narratives": self._build_narratives(
                profile=profile,
                analysis=analysis,
                ml_prediction=ml_from_db,
                xai=None,
                alerts=analysis.get("alerts"),
                goals=analysis.get("weekly_goals"),
                clinical_summary=None,
                health_plan=health_plan,
                predictions=self._extract_predictions_from_db(predictions),
                language=lang,
            ),
        }

    # ──────────────────────────────────────────────
    # Section builders
    # ──────────────────────────────────────────────

    def _build_profile_section(self, profile, language="es"):
        p = profile or {}
        return {
            "age": p.get("age"),
            "gender": p.get("gender"),
            "gender_label": _label_map(GENDER_LABELS, p.get("gender"), language),
            "height_cm": p.get("height_cm"),
            "weight_kg": p.get("weight_kg"),
            "activity_level": p.get("activity_level"),
            "activity_label": _label_map(
                ACTIVITY_LABELS, p.get("activity_level"), language
            ),
            "sleep_hours": p.get("sleep_hours"),
            "smokes": p.get("smokes", False),
            "has_chronic_conditions": p.get("has_chronic_conditions", False),
            "chronic_conditions_detail": p.get("chronic_conditions_detail"),
            "chronic_diseases": p.get("chronic_diseases") or [],
            "genetic_risk_factors": p.get("genetic_risk_factors") or [],
            "genetics_risk": p.get("genetics_risk", "low"),
            "health_goals": p.get("health_goals") or [],
            "family_history": p.get("family_history", False),
            "favc": p.get("favc"),
            "fcvc": p.get("fcvc"),
            "ch2o": p.get("ch2o"),
            "email": p.get("email"),
        }

    def _build_analysis_section(self, analysis, language="es"):
        a = analysis or {}
        bmi_category = a.get("bmi_category", "normal")
        desc_map = BMI_CATEGORY_DESCRIPTIONS.get(_lang(language), BMI_CATEGORY_DESCRIPTIONS["es"])
        return {
            "health_score": a.get("health_score", 0),
            "bmi": a.get("bmi", 0),
            "bmi_category": bmi_category,
            "bmi_label": get_bmi_category_label(bmi_category, language),
            "bmi_description": desc_map.get(bmi_category, ""),
            "bmr": a.get("bmr", 0),
            "tdee": a.get("tdee", 0),
            "health_risk": a.get("health_risk", ""),
            "health_risk_label": a.get("health_risk", ""),
            "fitness_level": a.get("fitness_level", ""),
            "next_checkup": a.get("next_checkup", ""),
            "confidence_score": a.get("confidence_score", 0),
            "analyzed_at": a.get("analyzed_at", ""),
        }

    def _build_ml_section(self, ml_prediction):
        ml = ml_prediction or {}
        if not ml.get("predicted_class") and ml.get("predicted_class") != 0:
            return {
                "available": False,
                "predicted_class": None,
                "predicted_class_label": None,
                "confidence": 0,
                "model_used": "none",
                "inference_time_ms": 0,
                "probabilities": {},
            }
        predicted_class = ml.get("predicted_class", "")
        return {
            "available": True,
            "predicted_class": predicted_class,
            "predicted_class_label": (
                predicted_class.replace("_", " ") if predicted_class else ""
            ),
            "confidence": ml.get("confidence", 0),
            "model_used": ml.get("model_used", "none"),
            "inference_time_ms": ml.get("inference_time_ms", 0),
            "probabilities": ml.get("probabilities") or {},
        }

    def _build_xai_section(self, xai):
        x = xai or {}
        if not x:
            return {
                "available": False,
                "summary": None,
                "main_reason": None,
                "confidence_text": None,
                "risk_explanation": None,
                "recommendations": [],
                "important_features": [],
                "scenario_follow": None,
                "scenario_ignore": None,
            }
        return {
            "available": True,
            "summary": x.get("summary"),
            "main_reason": x.get("main_reason"),
            "confidence_text": x.get("confidence_text"),
            "risk_explanation": x.get("risk_explanation"),
            "recommendations": x.get("recommendations") or [],
            "important_features": x.get("important_features") or [],
            "scenario_follow": x.get("scenario_follow"),
            "scenario_ignore": x.get("scenario_ignore"),
        }

    def _build_alerts_section(self, alerts):
        alerts_list = alerts or []
        result = []
        for alert in alerts_list:
            result.append({
                "type": alert.get("type", ""),
                "message": alert.get("message", ""),
                "priority": alert.get("priority", "low"),
                "icon": alert.get("icon", ""),
            })
        high = [a for a in result if a["priority"] == "high"]
        medium = [a for a in result if a["priority"] == "medium"]
        low = [a for a in result if a["priority"] not in ("high", "medium")]
        return {
            "all": result,
            "high": high,
            "medium": medium,
            "low": low,
            "total_count": len(result),
            "high_count": len(high),
        }

    def _build_goals_section(self, weekly_goals, language="es"):
        goals = weekly_goals or []
        translated_goals = []
        t = get_translations(language)
        for goal in goals:
            if isinstance(goal, dict) and "key" in goal:
                template = t.get(goal["key"], goal["key"])
                params = goal.get("params", {})
                try:
                    translated = template.format(**params)
                except (KeyError, IndexError):
                    translated = template
                translated_goals.append(translated)
            elif isinstance(goal, str):
                translated_goals.append(goal)
            else:
                translated_goals.append(str(goal))
        return {
            "all": translated_goals,
            "count": len(translated_goals),
        }

    def _build_nutrition_section(self, health_plan):
        nutrition = {}
        if health_plan:
            nutrition = health_plan.get("nutrition") or {}
        macros = nutrition.get("macronutrients") or {}
        return {
            "daily_calories": nutrition.get("daily_calories", 0),
            "macronutrients": {
                "protein_g": macros.get("protein", 0),
                "carbs_g": macros.get("carbs", 0),
                "fats_g": macros.get("fats", 0),
            },
            "recommendations": nutrition.get("recommendations") or [],
            "calorie_note": nutrition.get("calorie_note", ""),
        }

    def _build_exercise_section(self, health_plan):
        exercise = {}
        if health_plan:
            exercise = health_plan.get("exercise") or {}
        return {
            "cardio": exercise.get("cardio", "N/A"),
            "strength": exercise.get("strength", "N/A"),
            "flexibility": exercise.get("flexibility", "N/A"),
            "fitness_level": exercise.get("fitness_level", ""),
        }

    def _build_predictions_section(self, predictions, analysis=None):
        pred_data = predictions or {}
        preds = pred_data.get("predictions_data", {}).get("predictions") or {}
        analysis = analysis or {}

        current_weight = (
            pred_data.get("profile_snapshot", {}).get("weight")
            or analysis.get("bmi")
        )

        return {
            "current_weight_kg": current_weight,
            "two_weeks_kg": preds.get("2_weeks", {}).get("weight_kg"),
            "one_month_kg": preds.get("1_month", {}).get("weight_kg"),
            "six_months_kg": preds.get("6_months", {}).get("weight_kg"),
            "model_used": pred_data.get("model_used", ""),
            "confidence_score": pred_data.get("confidence_score", 0),
            "raw": pred_data,
        }

    def _build_history_section(self, history):
        history_list = history or []
        entries = []
        for h in history_list:
            entries.append({
                "analyzed_at": h.get("analyzed_at", ""),
                "health_score": h.get("health_score", 0),
                "bmi": h.get("bmi"),
                "health_risk": h.get("health_risk", ""),
                "fitness_level": h.get("fitness_level", ""),
            })
        return {
            "entries": entries,
            "count": len(entries),
            "has_data": len(entries) > 0,
        }

    # ──────────────────────────────────────────────
    # Reconstruction helpers (DB → structured data)
    # ──────────────────────────────────────────────

    def _reconstruct_ml_from_predictions(self, predictions):
        if not predictions:
            return None
        model_used = predictions.get("model_used", "")
        if not model_used:
            return None
        confidence = predictions.get("confidence_score", 0)
        if isinstance(confidence, float) and confidence <= 1.0:
            confidence = round(confidence * 100, 1)
        return {
            "predicted_class": None,
            "confidence": confidence,
            "model_used": model_used,
            "inference_time_ms": 0,
            "probabilities": {},
        }

    def _extract_predictions_from_db(self, predictions):
        if not predictions:
            return None
        return {
            "predictions_data": predictions.get("predictions_data") or {},
            "model_used": predictions.get("model_used", ""),
            "confidence_score": predictions.get("confidence_score", 0),
            "profile_snapshot": predictions.get("profile_snapshot") or {},
        }

    # ──────────────────────────────────────────────
    # Narratives — Textos interpretativos (LLM-ready)
    # ──────────────────────────────────────────────

    def _build_narratives(
        self, profile, analysis, ml_prediction, xai, alerts,
        goals, clinical_summary, health_plan, predictions,
        language="es",
    ):
        """
        Genera narratives interpretativas centralizadas (ES/EN).
        """
        lang = _lang(language)
        return {
            "clinical_summary": self._narrative_clinical_summary(
                analysis, clinical_summary, lang
            ),
            "bmi_interpretation": self._narrative_bmi_interpretation(analysis, lang),
            "risk_interpretation": self._narrative_risk_interpretation(
                analysis, alerts, lang
            ),
            "ml_interpretation": self._narrative_ml_interpretation(
                ml_prediction, xai, lang
            ),
            "recommendations_summary": self._narrative_recommendations(
                goals, alerts, health_plan, lang
            ),
            "prognosis": self._narrative_prognosis(
                predictions, analysis, xai, lang
            ),
        }

    def _narrative_clinical_summary(self, analysis, clinical_summary, language="es"):
        a = analysis or {}
        t = get_translations(language)
        health_score = a.get("health_score", 0)
        severity = a.get("health_risk", "")
        bmi = a.get("bmi", 0)
        bmi_category = a.get("bmi_category", "normal")
        bmi_label = get_bmi_category_label(bmi_category, language)
        fitness = a.get("fitness_level", "")

        if clinical_summary:
            text = clinical_summary.get("description", "")
            title = clinical_summary.get("title", t["narrative_summary"])
        else:
            title = t["narrative_summary"]
            if language == "en":
                if health_score >= 80:
                    text = (
                        f"The patient shows good health status with a "
                        f"score of {health_score}/100. "
                    )
                elif health_score >= 60:
                    text = (
                        f"The patient shows moderate health status with a "
                        f"score of {health_score}/100. "
                    )
                else:
                    text = (
                        f"The patient shows a health status that requires "
                        f"attention, with a score of {health_score}/100. "
                    )
                text += (
                    f"Clinical risk level is '{severity}'. "
                    f"BMI classification: {bmi_label} (BMI {bmi})."
                )
            else:
                if health_score >= 80:
                    text = (
                        f"El paciente presenta un buen estado de salud con un "
                        f"puntaje de {health_score}/100. "
                    )
                elif health_score >= 60:
                    text = (
                        f"El paciente presenta un estado de salud moderado con un "
                        f"puntaje de {health_score}/100. "
                    )
                else:
                    text = (
                        f"El paciente presenta un estado de salud que requiere "
                        f"atención, con un puntaje de {health_score}/100. "
                    )
                text += (
                    f"El nivel de riesgo clínico es '{severity}'. "
                    f"Clasificación BMI: {bmi_label} (IMC {bmi})."
                )

        return {
            "title": title,
            "text": text,
            "type": "clinical_summary",
            "llm_replaceable": True,
            "context": {
                "health_score": health_score,
                "severity": severity,
                "bmi": bmi,
                "bmi_category": bmi_category,
                "bmi_label": bmi_label,
                "fitness_level": fitness,
                "clinical_summary_raw": clinical_summary,
            },
        }

    def _narrative_bmi_interpretation(self, analysis, language="es"):
        a = analysis or {}
        t = get_translations(language)
        bmi = a.get("bmi", 0)
        bmi_category = a.get("bmi_category", "normal")
        bmi_label = get_bmi_category_label(bmi_category, language)
        desc_map = BMI_CATEGORY_DESCRIPTIONS.get(
            _lang(language), BMI_CATEGORY_DESCRIPTIONS["es"]
        )
        bmi_desc = desc_map.get(bmi_category, "")

        if language == "en":
            text = f"Current BMI is {bmi}, corresponding to {bmi_label}. {bmi_desc}"
        else:
            text = f"El IMC actual es {bmi}, correspondiente a {bmi_label}. {bmi_desc}"

        return {
            "title": t["narrative_bmi"],
            "text": text,
            "type": "bmi_interpretation",
            "llm_replaceable": True,
            "context": {
                "bmi": bmi,
                "bmi_category": bmi_category,
                "bmi_label": bmi_label,
                "bmi_description": bmi_desc,
            },
        }

    def _narrative_risk_interpretation(self, analysis, alerts, language="es"):
        a = analysis or {}
        t = get_translations(language)
        severity = a.get("health_risk", "")
        health_score = a.get("health_score", 0)
        severity_lower = severity.lower() if severity else "medium"
        sev_map = SEVERITY_DESCRIPTIONS.get(
            _lang(language), SEVERITY_DESCRIPTIONS["es"]
        )

        risk_text = sev_map.get(severity_lower, "")
        if not risk_text:
            for key in sev_map:
                if key in severity_lower:
                    risk_text = sev_map[key]
                    break
            if not risk_text:
                risk_text = sev_map["medium"]

        high_alerts = [
            al for al in (alerts or []) if al.get("priority") == "high"
        ]
        alert_note = ""
        if high_alerts:
            msgs = [al.get("message", "") for al in high_alerts[:2]]
            alert_note = " " + " ".join(msgs)

        text = f"{risk_text}{alert_note}"

        return {
            "title": t["narrative_risk"],
            "text": text,
            "type": "risk_interpretation",
            "llm_replaceable": True,
            "context": {
                "severity": severity,
                "health_score": health_score,
                "high_alert_messages": [
                    al.get("message", "") for al in high_alerts
                ],
            },
        }

    def _narrative_ml_interpretation(self, ml_prediction, xai, language="es"):
        ml = ml_prediction or {}
        x = xai or {}
        t = get_translations(language)

        predicted_class = ml.get("predicted_class") or ""
        confidence = ml.get("confidence", 0)
        ml_available = bool(predicted_class)

        if not ml_available:
            text = (
                "No ML model prediction is available for this analysis."
                if language == "en"
                else "No hay predicción del modelo ML disponible para este análisis."
            )
            return {
                "title": t["narrative_ml"],
                "text": text,
                "type": "ml_interpretation",
                "llm_replaceable": True,
                "context": {"available": False},
            }

        class_label = predicted_class.replace("_", " ") if predicted_class else ""
        if language == "en":
            text = (
                f"The ML model classifies the patient as '{class_label}' "
                f"with {confidence}% confidence."
            )
        else:
            text = (
                f"El modelo ML clasifica al paciente como '{class_label}' "
                f"con un {confidence}% de confianza."
            )

        if x.get("summary"):
            text += f" {x['summary']}"
        if x.get("main_reason"):
            text += f" {x['main_reason']}"

        return {
            "title": t["narrative_ml"],
            "text": text,
            "type": "ml_interpretation",
            "llm_replaceable": True,
            "context": {
                "available": True,
                "predicted_class": predicted_class,
                "predicted_class_label": class_label,
                "confidence": confidence,
                "model_used": ml.get("model_used", ""),
                "xai_summary": x.get("summary"),
                "xai_main_reason": x.get("main_reason"),
            },
        }

    def _narrative_recommendations(self, goals, alerts, health_plan, language="es"):
        t = get_translations(language)
        parts = []

        goals_list = goals or []
        if goals_list:
            parts.append(
                "Recommended weekly objectives:" if language == "en"
                else "Objetivos semanales recomendados:"
            )
            for g in goals_list[:5]:
                parts.append(f"- {g}")

        high_alerts = [
            al for al in (alerts or []) if al.get("priority") == "high"
        ]
        if high_alerts:
            parts.append(
                "Priority concerns:" if language == "en" else "Atenciones prioritarias:"
            )
            for al in high_alerts[:2]:
                msg = al.get("message", "")
                if msg:
                    parts.append(f"- {msg}")

        nutrition = {}
        if health_plan:
            nutrition = health_plan.get("nutrition") or {}
        recs = nutrition.get("recommendations") or []
        if recs:
            parts.append(
                "Nutrition recommendations:" if language == "en"
                else "Recomendaciones nutricionales:"
            )
            for r in recs[:3]:
                parts.append(f"- {r}")

        if not parts:
            parts.append(
                "Maintain healthy habits and schedule periodic follow-up."
                if language == "en"
                else "Mantener hábitos saludables y realizar seguimiento periódico."
            )

        text = "\n".join(parts)

        return {
            "title": t["narrative_recs"],
            "text": text,
            "type": "recommendations_summary",
            "llm_replaceable": True,
            "context": {
                "goals": goals_list,
                "high_alert_messages": [
                    al.get("message", "") for al in high_alerts
                ],
                "nutrition_recommendations": recs,
            },
        }

    def _narrative_prognosis(self, predictions, analysis, xai, language="es"):
        p = predictions or {}
        preds = p.get("predictions_data", {}).get("predictions") or {}
        a = analysis or {}
        x = xai or {}
        t = get_translations(language)

        six_months = preds.get("6_months", {}).get("weight_kg")
        one_month = preds.get("1_month", {}).get("weight_kg")
        current_bmi = a.get("bmi", 0)
        bmi_category = a.get("bmi_category", "normal")
        text = ""

        if x and x.get("scenario_follow"):
            sf = x["scenario_follow"]
            text = sf.get("evolution_text", "")
            if sf.get("projected_category"):
                proj_label = get_bmi_category_label(
                    sf.get("projected_category"), language
                )
                if language == "en":
                    text += (
                        f" Projected at 6 months: BMI {sf.get('projected_bmi', '')} "
                        f"({proj_label})."
                    )
                else:
                    text += (
                        f" Proyectado a 6 meses: IMC {sf.get('projected_bmi', '')} "
                        f"({proj_label})."
                    )

        if not text and six_months and six_months >= 30:
            if language == "en":
                text = (
                    f"6-month projection: estimated weight {six_months} kg. "
                    f"Following the current plan, stabilization or gradual "
                    f"improvement is expected."
                )
            else:
                text = (
                    f"Proyección a 6 meses: peso estimado {six_months} kg. "
                    f"Siguiendo el plan actual, se espera estabilización "
                    f"o mejora gradual."
                )

        if not text:
            text = (
                "There is not enough data to generate a prognosis. "
                "A new analysis is recommended to establish projections."
                if language == "en"
                else (
                    "No hay suficientes datos para generar un pronóstico. "
                    "Se recomienda un nuevo análisis para establecer proyecciones."
                )
            )

        return {
            "title": t["narrative_prognosis"],
            "text": text,
            "type": "prognosis",
            "llm_replaceable": True,
            "context": {
                "current_weight_kg": a.get("bmi"),
                "projected_6m_kg": six_months,
                "projected_1m_kg": one_month,
                "current_bmi": current_bmi,
                "current_bmi_category": bmi_category,
                "scenario_follow": x.get("scenario_follow") if x else None,
                "scenario_ignore": x.get("scenario_ignore") if x else None,
            },
        }
