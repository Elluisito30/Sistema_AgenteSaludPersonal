"""
Excel Renderer — Generacion de reportes Excel con XlsxWriter.

Solo renderiza. No accede a BD, no accede al modelo ML, no recalcula.
Consume exclusivamente report_data (dict de ReportEngine).
"""

import io
from datetime import datetime

import xlsxwriter

from services.reports.styles import get_translations, COLORS, BMI_CATEGORY_COLORS
from services.reports.helpers import (
    format_risk_badge,
    format_confidence_badge,
    format_bmi_indicator,
    format_weight_projection,
    format_macronutrients,
    format_exercise_plan,
    format_profile_summary,
    format_history_entries,
)


def _header_format(workbook):
    return workbook.add_format({
        "bold": True, "bg_color": COLORS["primary_dark"],
        "font_color": "white", "border": 1,
    })


def _cell_format(workbook):
    return workbook.add_format({"border": 1, "bg_color": COLORS["background_light"]})


def _title_format(workbook):
    return workbook.add_format({
        "bold": True, "font_size": 14, "font_color": COLORS["primary_dark"],
    })


def _subtitle_format(workbook):
    return workbook.add_format({
        "bold": True, "font_size": 11, "font_color": COLORS["primary_medium"],
    })


def _risk_formats(workbook):
    return {
        "critical": workbook.add_format({"bg_color": "#ffc7ce", "font_color": "#9c0006"}),
        "high": workbook.add_format({"bg_color": "#ffeb9c", "font_color": "#9c6500"}),
        "medium": workbook.add_format({"bg_color": "#ffeb9c", "font_color": "#9c6500"}),
        "low": workbook.add_format({"bg_color": "#c6efce", "font_color": "#006100"}),
    }


# ==========================================
# HEALTH REPORT EXCEL
# ==========================================

def generate_health_excel(report_data, language="es"):
    t = get_translations(language)
    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"in_memory": True})
    hf = _header_format(wb)
    cf = _cell_format(wb)
    rf = _risk_formats(wb)

    profile_info = format_profile_summary(report_data.get("profile"))
    analysis = report_data.get("analysis", {})
    risk_badge = format_risk_badge(analysis.get("health_risk"), language)
    bmi_ind = format_bmi_indicator(analysis.get("bmi"), analysis.get("bmi_category"))

    # HOJA 1: METRICAS
    ws1 = wb.add_worksheet(t["metrics"] if "metrics" in t else "Metricas")
    ws1.set_column("A:B", 25)
    ws1.write(0, 0, t["indicator"], hf)
    ws1.write(0, 1, t["value"], hf)

    metrics = [
        (t["health_score"], analysis.get("health_score", 0)),
        (t["risk_level"], risk_badge["label"]),
        (t["bmi"], f"{bmi_ind['value']} ({bmi_ind['label']})"),
        (t["bmr"], analysis.get("bmr", 0)),
        (t["tdee"], analysis.get("tdee", 0)),
        (t["fitness_level"], analysis.get("fitness_level", "")),
    ]
    for row_num, (ind, val) in enumerate(metrics, 1):
        ws1.write(row_num, 0, ind, cf)
        ws1.write(row_num, 1, val, cf)

    # HOJA 2: HISTORIAL
    history_entries = format_history_entries(report_data.get("history"))
    ws2 = wb.add_worksheet(t["history"])
    ws2.set_column("A:D", 20)
    ws2.write_row(0, 0, ["Fecha", t["health_score"], t["risk_level"], t["bmi"]], hf)
    for row_num, h in enumerate(history_entries, 1):
        ws2.write(row_num, 0, h["date"], cf)
        ws2.write(row_num, 1, h["health_score"], cf)
        ws2.write(row_num, 2, h["health_risk"], cf)
        ws2.write(row_num, 3, h.get("bmi", ""), cf)

    if history_entries:
        last_row = len(history_entries) + 1
        ws2.conditional_format(
            f"B2:B{last_row}",
            {"type": "cell", "criteria": "<=", "value": 40, "format": rf["critical"]},
        )
        ws2.conditional_format(
            f"B2:B{last_row}",
            {"type": "cell", "criteria": ">=", "value": 81, "format": rf["low"]},
        )

    # HOJA 3: FACTORES DE RIESGO
    ws3 = wb.add_worksheet(t["clinical_factors"])
    ws3.set_column("A:B", 30)
    ws3.write_row(0, 0, [t["category"], t["detected_conditions"]], hf)
    profile = report_data.get("profile", {})
    ws3.write(1, 0, t["chronic"], cf)
    ws3.write(1, 1, ", ".join(profile.get("chronic_diseases", [])) or t["no_data"], cf)
    ws3.write(2, 0, t["genetics"], cf)
    ws3.write(2, 1, ", ".join(profile.get("genetic_risk_factors", [])) or t["no_data"], cf)

    # HOJA 4: ALERTAS
    alerts_data = report_data.get("alerts", {})
    all_alerts = alerts_data.get("all", [])
    if all_alerts:
        ws4 = wb.add_worksheet(t["alerts"])
        ws4.set_column("A:C", 25)
        ws4.write_row(0, 0, [t["type"], "Mensaje", t["value"]], hf)
        for i, al in enumerate(all_alerts[:10], 1):
            ws4.write(i, 0, al.get("type", ""), cf)
            ws4.write(i, 1, al.get("message", ""), cf)
            ws4.write(i, 2, al.get("priority", ""), cf)

    # HOJA 5: OBJETIVOS
    goals = report_data.get("goals", {}).get("all", [])
    if goals:
        ws5 = wb.add_worksheet(t["objectives"])
        ws5.set_column("A:B", 30)
        ws5.write(0, 0, "Objetivo", hf)
        for i, g in enumerate(goals[:10], 1):
            ws5.write(i, 0, g, cf)

    # HOJA 6: NARRATIVAS
    narratives = report_data.get("narratives", {})
    ws6 = wb.add_worksheet("Narrativas")
    ws6.set_column("A:B", 40)
    ws6.write(0, 0, "Seccion", hf)
    ws6.write(0, 1, "Texto", hf)
    row = 1
    for nk in ["clinical_summary", "bmi_interpretation", "risk_interpretation",
               "ml_interpretation", "recommendations_summary", "prognosis"]:
        nav = narratives.get(nk)
        if nav:
            ws6.write(row, 0, nav.get("title", ""), cf)
            ws6.write(row, 1, nav.get("text", ""), cf)
            row += 1

    wb.close()
    buf.seek(0)
    return buf


# ==========================================
# PREDICTIONS REPORT EXCEL
# ==========================================

def generate_predictions_excel(report_data, language="es"):
    t = get_translations(language)
    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"in_memory": True})
    hf = _header_format(wb)
    cf = _cell_format(wb)

    # HOJA 1: PROYECCIONES
    ws1 = wb.add_worksheet(t["predictions_report"])
    ws1.set_column("A:B", 25)
    ws1.write(0, 0, t["period"], hf)
    ws1.write(0, 1, t["weight"], hf)

    wp = format_weight_projection(report_data.get("predictions"))
    if wp.get("available"):
        for i, p in enumerate(wp["periods"], 1):
            ws1.write(i, 0, p["label"], cf)
            ws1.write(i, 1, f"{p['weight_kg']} kg", cf)

    # HOJA 2: ML
    ml = report_data.get("ml_prediction", {})
    if ml.get("available"):
        ws2 = wb.add_worksheet(t["ml_prediction"])
        ws2.set_column("A:B", 25)
        ws2.write(0, 0, t["metric"], hf)
        ws2.write(0, 1, t["value"], hf)
        conf = format_confidence_badge(ml.get("confidence", 0))
        ws2.write(1, 0, "Clasificacion", cf)
        ws2.write(1, 1, ml.get("predicted_class_label", ""), cf)
        ws2.write(2, 0, t["confidence"], cf)
        ws2.write(2, 1, conf["label"], cf)
        ws2.write(3, 0, t["model"], cf)
        ws2.write(3, 1, ml.get("model_used", ""), cf)

    # HOJA 3: NARRATIVAS
    narratives = report_data.get("narratives", {})
    ws3 = wb.add_worksheet("Narrativas")
    ws3.set_column("A:B", 40)
    ws3.write(0, 0, "Seccion", hf)
    ws3.write(0, 1, "Texto", hf)
    row = 1
    for nk in ["ml_interpretation", "prognosis"]:
        nav = narratives.get(nk)
        if nav:
            ws3.write(row, 0, nav.get("title", ""), cf)
            ws3.write(row, 1, nav.get("text", ""), cf)
            row += 1

    wb.close()
    buf.seek(0)
    return buf


# ==========================================
# NUTRITION REPORT EXCEL
# ==========================================

def generate_nutrition_excel(report_data, language="es"):
    t = get_translations(language)
    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"in_memory": True})
    hf = _header_format(wb)
    cf = _cell_format(wb)

    macros = format_macronutrients(report_data.get("nutrition"))

    ws1 = wb.add_worksheet(t["nutrition_summary"])
    ws1.set_column("A:B", 25)
    ws1.write(0, 0, t["metric"], hf)
    ws1.write(0, 1, t["value"], hf)
    if macros.get("available"):
        ws1.write(1, 0, t["daily_calories"], cf)
        ws1.write(1, 1, f"{macros['daily_calories']} kcal", cf)
        ws1.write(2, 0, t["protein"], cf)
        ws1.write(2, 1, f"{macros['protein_g']} g", cf)
        ws1.write(3, 0, t["carbs"], cf)
        ws1.write(3, 1, f"{macros['carbs_g']} g", cf)
        ws1.write(4, 0, t["fats"], cf)
        ws1.write(4, 1, f"{macros['fats_g']} g", cf)

    ws2 = wb.add_worksheet(t["suggested_recipes"])
    ws2.set_column("A:C", 25)
    ws2.write_row(0, 0, [t["meal"], t["recipe"], t["protein_g"]], hf)
    if macros.get("available"):
        protein = macros["protein_g"]
        recipes = [
            (t["breakfast"], "Avena con frutas frescas, chia y nueces" if language == "es" else "Oatmeal with fruits, chia and nuts", round(protein * 0.2)),
            (t["lunch"], "Pechuga de pollo con quinoa y vegetales" if language == "es" else "Grilled chicken with quinoa and vegetables", round(protein * 0.4)),
            (t["dinner"], "Ensalada de salmon con aguacate" if language == "es" else "Salmon salad with avocado", round(protein * 0.3)),
            (t["snack"], "Yogur griego o almendras" if language == "es" else "Greek yogurt or almonds", round(protein * 0.1)),
        ]
        for i, (meal, recipe, prot) in enumerate(recipes, 1):
            ws2.write(i, 0, meal, cf)
            ws2.write(i, 1, recipe, cf)
            ws2.write(i, 2, prot, cf)

    wb.close()
    buf.seek(0)
    return buf


# ==========================================
# EXERCISE REPORT EXCEL
# ==========================================

def generate_exercise_excel(report_data, language="es"):
    t = get_translations(language)
    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"in_memory": True})
    hf = _header_format(wb)
    cf = _cell_format(wb)

    ws1 = wb.add_worksheet(t["exercise_plan"])
    ws1.set_column("A:B", 25)
    ws1.write(0, 0, t["type"], hf)
    ws1.write(0, 1, t["duration"], hf)

    ex = format_exercise_plan(report_data.get("exercise"))
    if ex.get("available"):
        rows = [
            (t["cardio"], ex["cardio"]),
            (t["strength"], ex["strength"]),
            (t["flexibility"], ex["flexibility"]),
        ]
        for i, (tipo, duracion) in enumerate(rows, 1):
            ws1.write(i, 0, tipo, cf)
            ws1.write(i, 1, duracion, cf)

    wb.close()
    buf.seek(0)
    return buf
