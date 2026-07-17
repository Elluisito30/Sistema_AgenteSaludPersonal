"""
XAI Service — Servicio de IA Explicable (puramente interpretativo).

NO recalcula BMI, severidad, health_score ni predicciones.
NO modifica RecommendationEngine ni PredictionRules.
Únicamente interpreta los resultados existentes y los traduce a lenguaje natural.

Entrada: datos ya generados por el sistema (ml_prediction, health_score,
         clinical_summary, alerts, predictions, weekly_goals, importance.json).
Salida:  dict con explicación comprensible para el usuario.
"""

import os
import json


BMI_CATEGORY_LABELS = {
    "severely_underweight": "delgadez severa",
    "underweight": "bajo peso",
    "normal": "peso normal",
    "overweight": "sobrepeso",
    "obese_1": "obesidad grado I",
    "obese_2_3": "obesidad grado II/III",
}

BMI_CATEGORY_DESCRIPTORS = {
    "severely_underweight": "un peso significativamente por debajo del rango saludable",
    "underweight": "un peso por debajo del rango saludable",
    "normal": "un peso dentro del rango saludable",
    "overweight": "un peso ligeramente por encima del rango saludable",
    "obese_1": "un nivel de obesidad grado I",
    "obese_2_3": "un nivel avanzado de obesidad",
}

RISK_EXPLANATIONS = {
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
}

CONFIDENCE_TEXTS = [
    (95, "El modelo presenta una confianza muy alta en esta clasificación."),
    (80, "El modelo presenta una confianza alta en esta clasificación."),
    (60, "El modelo presenta una confianza moderada. Los resultados deben interpretarse como una guía."),
    (0,  "La confianza del modelo es baja. Se recomienda contrastar con una evaluación clínica profesional."),
]


class XAIService:
    """
    Singleton puramente interpretativo.
    Recibe datos existentes del sistema y los traduce a explicaciones comprensibles.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.importance_data = self._load_importance()

    def _get_models_dir(self):
        docker_path = "/app/models"
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))),
            "eda", "models",
        )
        if os.path.isdir(docker_path):
            return docker_path
        return local_path

    def _load_importance(self):
        path = os.path.join(self._get_models_dir(), "importance.json")
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"XAI importance loaded: {len(data)} features from {path}")
            return data
        print(f"XAI importance not found at {path} — feature importance disabled")
        return []

    # ── Generadores de texto ──────────────────────────────────────────────

    def _build_summary(self, ml_prediction, clinical_summary, bmi, bmi_category):
        ml_class = (ml_prediction.get("predicted_class") or "").replace("_", " ")
        cs_title = clinical_summary.get("title", "") if clinical_summary else ""
        cs_desc = clinical_summary.get("description", "") if clinical_summary else ""
        bmi_label = clinical_summary.get("bmi_label", "") if clinical_summary else ""

        if not ml_class:
            return cs_desc or "No hay clasificación ML disponible para generar el resumen."

        category_text = BMI_CATEGORY_LABELS.get(bmi_category, "una categoría no determinada")
        parts = [
            f"La clasificación inteligente indica {category_text}.",
        ]
        if bmi_label:
            parts.append(f"Etiqueta clínica: {bmi_label}.")
        if cs_title and cs_title != bmi_label:
            parts.append(f"{cs_title}.")

        return " ".join(parts)

    def _build_main_reason(self, ml_prediction, importance_data, bmi, activity_level):
        confidence = ml_prediction.get("confidence", 0)
        ml_class = (ml_prediction.get("predicted_class") or "").replace("_", " ")

        top_features = importance_data[:3] if importance_data else []
        feature_mentions = []
        for feat in top_features:
            fname = feat.get("display_name", feat.get("feature", ""))
            imp = feat.get("importance", 0)
            if imp > 0.05:
                feature_mentions.append(fname)
            elif imp > 0.01:
                feature_mentions.append(fname)

        if not feature_mentions:
            return (
                f"La clasificación {ml_class} se basa en el análisis "
                f"combinado de las variables del perfil."
            )

        factors_text = ", ".join(feature_mentions[:3])
        return (
            f"La clasificación {ml_class} se fundamenta principalmente "
            f"en {factors_text}."
        )

    def _build_confidence_text(self, confidence):
        for threshold, text in CONFIDENCE_TEXTS:
            if confidence >= threshold:
                return text
        return CONFIDENCE_TEXTS[-1][1]

    def _build_risk_explanation(self, severity, alerts, clinical_summary):
        risk_text = RISK_EXPLANATIONS.get(severity, RISK_EXPLANATIONS["medium"])

        high_alerts = [a for a in (alerts or []) if a.get("priority") == "high"]
        if high_alerts:
            alert_messages = [a.get("message", "") for a in high_alerts[:2]]
            risk_text += " " + " ".join(alert_messages)

        return risk_text

    def _build_recommendations(self, weekly_goals, alerts, bmi_category):
        recs = []
        for goal in (weekly_goals or [])[:5]:
            recs.append(goal)

        high_alerts = [a for a in (alerts or []) if a.get("priority") == "high"]
        for alert in high_alerts[:2]:
            msg = alert.get("message", "")
            if msg and msg not in recs:
                recs.append(f"Atención: {msg}")

        if not recs:
            recs.append("Mantener hábitos saludables y realizar seguimiento periódico.")

        return recs

    def _build_important_features(self, importance_data, ml_prediction):
        result = []
        for feat in (importance_data or [])[:5]:
            imp = feat.get("importance", 0)
            if imp >= 0.10:
                level = "high"
            elif imp >= 0.02:
                level = "medium"
            else:
                level = "low"
            result.append({
                "feature": feat.get("feature", ""),
                "display_name": feat.get("display_name", feat.get("feature", "")),
                "importance": imp,
                "level": level,
            })
        return result

    def _get_bmi_category_for_weight(self, weight_kg, height_cm):
        if height_cm <= 0:
            return "normal"
        bmi = weight_kg / ((height_cm / 100) ** 2)
        if bmi < 16:
            return "severely_underweight"
        if bmi < 18.5:
            return "underweight"
        if bmi < 25:
            return "normal"
        if bmi < 30:
            return "overweight"
        if bmi < 35:
            return "obese_1"
        return "obese_2_3"

    def _build_scenario_follow(self, predictions, height_cm, bmi_category):
        pred_data = (predictions or {}).get("predictions_data", {})
        preds = pred_data.get("predictions", {})

        six_months = preds.get("6_months", {})
        one_month = preds.get("1_month", {})
        proj_weight = six_months.get("weight_kg") or one_month.get("weight_kg")

        if not proj_weight or not height_cm:
            return None

        proj_bmi = round(proj_weight / ((height_cm / 100) ** 2), 1)
        proj_category = self._get_bmi_category_for_weight(proj_weight, height_cm)
        proj_label = BMI_CATEGORY_LABELS.get(proj_category, proj_category)

        category_improved = (
            list(BMI_CATEGORY_LABELS.keys()).index(proj_category)
            > list(BMI_CATEGORY_LABELS.keys()).index(bmi_category)
            if proj_category in BMI_CATEGORY_LABELS
               and bmi_category in BMI_CATEGORY_LABELS
            else False
        )

        if proj_category == bmi_category:
            evolution = (
                "Se espera que la categoría clínica se mantenga estable."
            )
        elif category_improved:
            evolution = (
                f"Se espera una mejora hacia {proj_label} "
                f"si se mantienen los hábitos actuales."
            )
        else:
            evolution = (
                f"La categoría clínica podría avanzar a {proj_label}."
            )

        return {
            "title": "Si sigue el plan",
            "projected_weight_kg": proj_weight,
            "projected_bmi": proj_bmi,
            "projected_category": proj_label,
            "evolution_text": evolution,
            "weight_change_kg": round(proj_weight - (predictions or {}).get("predictions_data", {}).get("predictions", {}).get("2_weeks", {}).get("weight_kg", proj_weight), 1)
            if preds.get("2_weeks", {}).get("weight_kg") else 0,
        }

    def _build_scenario_ignore(self, predictions, height_cm, bmi_category, weight_kg):
        pred_data = (predictions or {}).get("predictions_data", {})
        preds = pred_data.get("predictions", {})

        six_months = preds.get("6_months", {})
        one_month = preds.get("1_month", {})
        proj_weight = six_months.get("weight_kg") or one_month.get("weight_kg")

        if not proj_weight or not height_cm or not weight_kg:
            return None

        model_used = (predictions or {}).get("model_used", "")
        if "hybrid" in model_used:
            ignore_weight = round(weight_kg + (weight_kg - proj_weight), 1)
        else:
            strategy_indicator = 1 if bmi_category in [
                "overweight", "obese_1", "obese_2_3"
            ] else -1
            ignore_weight = round(weight_kg + (weight_kg - proj_weight) * strategy_indicator, 1)

        ignore_weight = max(30.0, ignore_weight)
        ignore_bmi = round(ignore_weight / ((height_cm / 100) ** 2), 1)
        ignore_category = self._get_bmi_category_for_weight(ignore_weight, height_cm)
        ignore_label = BMI_CATEGORY_LABELS.get(ignore_category, ignore_category)

        category_worsened = (
            list(BMI_CATEGORY_LABELS.keys()).index(ignore_category)
            < list(BMI_CATEGORY_LABELS.keys()).index(bmi_category)
            if ignore_category in BMI_CATEGORY_LABELS
               and bmi_category in BMI_CATEGORY_LABELS
            else False
        )

        if ignore_category == bmi_category:
            risk_text = (
                "Sin cambios en los hábitos, el peso y la categoría clínica "
                "se mantendrían estables."
            )
        elif category_worsened:
            risk_text = (
                f"Sin cambios en los hábitos, existe riesgo de retroceso "
                f"hacia {ignore_label}."
            )
        else:
            risk_text = (
                f"Sin cambios, la categoría podría estabilizarse en {ignore_label}."
            )

        return {
            "title": "Si no sigue el plan",
            "projected_weight_kg": ignore_weight,
            "projected_bmi": ignore_bmi,
            "projected_category": ignore_label,
            "risk_text": risk_text,
        }

    # ── Método principal ──────────────────────────────────────────────────

    def generate_xai_explanation(
        self,
        age=None,
        gender=None,
        height_cm=None,
        weight_kg=None,
        bmi=None,
        bmi_category=None,
        activity_level=None,
        smokes=None,
        ml_prediction=None,
        health_score=None,
        severity=None,
        clinical_summary=None,
        alerts=None,
        predictions=None,
        weekly_goals=None,
    ):
        """
        Genera explicación XAI puramente interpretativa.
        NO recalcula BMI, severidad, health_score ni predicciones.
        """
        ml_prediction = ml_prediction or {}
        importance = self.importance_data

        summary = self._build_summary(ml_prediction, clinical_summary, bmi, bmi_category)
        main_reason = self._build_main_reason(ml_prediction, importance, bmi, activity_level)
        confidence = ml_prediction.get("confidence", 0)
        confidence_text = self._build_confidence_text(confidence)
        risk_explanation = self._build_risk_explanation(severity, alerts, clinical_summary)
        recommendations = self._build_recommendations(weekly_goals, alerts, bmi_category)
        important_features = self._build_important_features(importance, ml_prediction)

        scenario_follow = self._build_scenario_follow(predictions, height_cm, bmi_category)
        scenario_ignore = self._build_scenario_ignore(
            predictions, height_cm, bmi_category, weight_kg
        )

        return {
            "title": "Análisis Inteligente — Explicación de Predicción",
            "summary": summary,
            "main_reason": main_reason,
            "confidence_text": confidence_text,
            "risk_explanation": risk_explanation,
            "recommendations": recommendations,
            "important_features": important_features,
            "scenario_follow": scenario_follow,
            "scenario_ignore": scenario_ignore,
        }


xai_service = XAIService()
