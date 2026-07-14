"""
Helpers — Funciones de formato reutilizables para reportes.

Módulo puro de datos estructurados. Sin dependencias de renderizado.
Devuelve dicts/lists que cada renderer interpreta a su manera.
"""

from services.reports.styles import (
    get_risk_colors,
    ALERT_PRIORITY_COLORS,
    BMI_CATEGORY_LABELS,
    BMI_CATEGORY_COLORS,
    COLORS,
)


def format_risk_badge(risk_level, language="es"):
    """Badge de nivel de riesgo con color y label."""
    colors = get_risk_colors(risk_level)
    return {
        "label": risk_level or "Sin Datos",
        "color_hex": colors["hex"],
        "color_rgb": colors["rgb"],
    }


def format_confidence_badge(confidence):
    """Badge de confianza del modelo ML."""
    if confidence is None:
        confidence = 0
    if isinstance(confidence, float) and confidence <= 1.0:
        confidence = round(confidence * 100, 1)

    if confidence >= 90:
        color = COLORS["success"]
        level = "alta"
    elif confidence >= 70:
        color = COLORS["info"]
        level = "media"
    elif confidence >= 50:
        color = COLORS["warning"]
        level = "baja"
    else:
        color = COLORS["danger"]
        level = "muy baja"

    return {
        "value": confidence,
        "label": f"{confidence}%",
        "level": level,
        "color_hex": color,
    }


def format_bmi_indicator(bmi, bmi_category):
    """Indicador visual de BMI con barra de progreso."""
    if bmi is None:
        bmi = 0

    bmi_ranges = [
        (0, 16, 0),
        (16, 18.5, 27),
        (18.5, 25, 50),
        (25, 30, 67),
        (30, 35, 83),
        (35, 100, 100),
    ]

    progress = 50
    for min_val, max_val, pct in bmi_ranges:
        if min_val <= bmi < max_val:
            progress = pct
            break

    label = BMI_CATEGORY_LABELS.get(bmi_category, bmi_category or "")
    color = BMI_CATEGORY_COLORS.get(bmi_category, COLORS["text_light"])

    return {
        "value": round(bmi, 1) if bmi else 0,
        "label": label,
        "category": bmi_category,
        "color_hex": color,
        "progress_pct": progress,
    }


def format_weight_projection(predictions_section):
    """Proyecciones de peso formateadas."""
    if not predictions_section:
        return {"available": False}

    current = predictions_section.get("current_weight_kg")
    two_w = predictions_section.get("two_weeks_kg")
    one_m = predictions_section.get("one_month_kg")
    six_m = predictions_section.get("six_months_kg")

    periods = []
    if current is not None:
        periods.append({"label": "actual", "weight_kg": current, "change_kg": 0})
    if two_w is not None:
        change = round(two_w - current, 1) if current else 0
        periods.append({"label": "2 semanas", "weight_kg": two_w, "change_kg": change})
    if one_m is not None:
        change = round(one_m - current, 1) if current else 0
        periods.append({"label": "1 mes", "weight_kg": one_m, "change_kg": change})
    if six_m is not None:
        change = round(six_m - current, 1) if current else 0
        periods.append({"label": "6 meses", "weight_kg": six_m, "change_kg": change})

    return {
        "available": len(periods) > 1,
        "current_kg": current,
        "periods": periods,
        "model_used": predictions_section.get("model_used", ""),
        "confidence": predictions_section.get("confidence_score", 0),
    }


def format_alert_priority(priority, language="es"):
    """Badge de prioridad de alerta."""
    info = ALERT_PRIORITY_COLORS.get(priority, ALERT_PRIORITY_COLORS["low"])
    return {
        "priority": priority,
        "label": info.get(f"label_{language}", info["label_en"]),
        "color_hex": info["hex"],
        "color_rgb": info["rgb"],
    }


def format_macronutrients(nutrition_section):
    """Macronutrientes con distribución porcentual."""
    if not nutrition_section:
        return {"available": False}

    macros = nutrition_section.get("macronutrients") or {}
    protein = macros.get("protein_g", 0) or 0
    carbs = macros.get("carbs_g", 0) or 0
    fats = macros.get("fats_g", 0) or 0

    total_kcal = (protein * 4) + (carbs * 4) + (fats * 9)

    if total_kcal > 0:
        protein_pct = round((protein * 4 / total_kcal) * 100)
        carbs_pct = round((carbs * 4 / total_kcal) * 100)
        fats_pct = round((fats * 9 / total_kcal) * 100)
    else:
        protein_pct = carbs_pct = fats_pct = 0

    return {
        "available": True,
        "daily_calories": nutrition_section.get("daily_calories", 0),
        "protein_g": protein,
        "carbs_g": carbs,
        "fats_g": fats,
        "protein_pct": protein_pct,
        "carbs_pct": carbs_pct,
        "fats_pct": fats_pct,
        "recommendations": nutrition_section.get("recommendations") or [],
    }


def format_exercise_plan(exercise_section):
    """Plan de ejercicio formateado."""
    if not exercise_section:
        return {"available": False}

    return {
        "available": True,
        "cardio": exercise_section.get("cardio", "N/A"),
        "strength": exercise_section.get("strength", "N/A"),
        "flexibility": exercise_section.get("flexibility", "N/A"),
        "fitness_level": exercise_section.get("fitness_level", ""),
    }


def format_profile_summary(profile_section):
    """Resumen del perfil para encabezados de reporte."""
    if not profile_section:
        return {"display_name": "Usuario", "age_gender": "", "bmi_info": ""}

    email = profile_section.get("email") or "Usuario"
    name = email.split("@")[0] if "@" in email else email
    age = profile_section.get("age", "")
    gender = profile_section.get("gender_label", "")

    parts = []
    if age:
        parts.append(f"{age} anos")
    if gender:
        parts.append(gender)

    return {
        "display_name": name,
        "email": email,
        "age_gender": ", ".join(parts),
        "height_cm": profile_section.get("height_cm"),
        "weight_kg": profile_section.get("weight_kg"),
        "activity_level": profile_section.get("activity_label", ""),
    }


def format_history_entries(history_section):
    """Historial formateado para tablas."""
    if not history_section:
        return []

    entries = history_section.get("entries") or []
    result = []
    for entry in entries:
        analyzed_at = entry.get("analyzed_at", "")
        if isinstance(analyzed_at, str) and len(analyzed_at) >= 10:
            analyzed_at = analyzed_at[:10]
        result.append({
            "date": analyzed_at,
            "health_score": entry.get("health_score", 0),
            "bmi": entry.get("bmi"),
            "health_risk": entry.get("health_risk", ""),
        })
    return result


def format_scenarios(xai_section):
    """Escenarios futuro (seguir/ignorar plan)."""
    if not xai_section or not xai_section.get("available"):
        return {"follow": None, "ignore": None, "has_scenarios": False}

    follow = xai_section.get("scenario_follow")
    ignore = xai_section.get("scenario_ignore")

    return {
        "follow": follow,
        "ignore": ignore,
        "has_scenarios": bool(follow or ignore),
    }
