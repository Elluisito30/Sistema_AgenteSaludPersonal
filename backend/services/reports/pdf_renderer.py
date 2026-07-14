"""
PDF Renderer — Generacion de reportes PDF con ReportLab.

Solo renderiza. No accede a BD, no accede al modelo ML, no recalcula.
Consume exclusivamente report_data (dict de ReportEngine).
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from services.reports.styles import get_translations, get_risk_colors, COLORS
from services.reports.helpers import (
    format_risk_badge,
    format_confidence_badge,
    format_bmi_indicator,
    format_weight_projection,
    format_alert_priority,
    format_macronutrients,
    format_exercise_plan,
    format_profile_summary,
    format_scenarios,
)


# ──────────────────────────────────────────────
# Estilos PDF internos
# ──────────────────────────────────────────────

def _get_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "MainTitle", parent=base["Heading1"], fontSize=18,
            spaceAfter=20, textColor=colors.HexColor(COLORS["primary_dark"]),
            alignment=1,
        ),
        "subtitle": ParagraphStyle(
            "SubTitle", parent=base["Heading2"], fontSize=14,
            spaceAfter=10, textColor=colors.HexColor(COLORS["primary_medium"]),
        ),
        "normal": base["Normal"],
        "small": ParagraphStyle(
            "Small", parent=base["Normal"], fontSize=9,
            textColor=colors.HexColor(COLORS["text_light"]),
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", parent=base["Heading3"], fontSize=12,
            spaceAfter=8, spaceBefore=14,
            textColor=colors.HexColor(COLORS["primary_dark"]),
        ),
    }


def _make_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary_dark"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor(COLORS["background_light"])),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    return t


def _header_block(elements, t, profile_info):
    elements.append(Paragraph(
        f"{t['app_name']} - {t['health_report']}", t["_styles"]["title"]
    ))
    elements.append(Paragraph(
        f"<b>{t['date_generated']}:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        t["_styles"]["normal"],
    ))
    if profile_info.get("display_name"):
        elements.append(Paragraph(
            f"<b>{t['patient']}:</b> {profile_info['display_name']}",
            t["_styles"]["normal"],
        ))
    elements.append(Spacer(1, 20))


# ==========================================
# HEALTH REPORT PDF
# ==========================================

def generate_health_pdf(report_data, plot_bytes=None, language="es"):
    t = get_translations(language)
    t["_styles"] = _get_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))
    _header_block(elements, t, profile_info)

    # Seccion: Evaluacion de Riesgo
    analysis = report_data.get("analysis", {})
    risk_badge = format_risk_badge(analysis.get("health_risk"), language)
    bmi_ind = format_bmi_indicator(analysis.get("bmi"), analysis.get("bmi_category"))

    elements.append(Paragraph(t["risk_evaluation"], t["_styles"]["subtitle"]))
    metrics = [
        [t["metric"], t["value"]],
        [t["health_score"], f"{analysis.get('health_score', 0)} / 100"],
        [t["clinical_status"], risk_badge["label"]],
        [t["bmi"], f"{bmi_ind['value']} ({bmi_ind['label']})"],
        [t["bmr"], str(analysis.get("bmr", 0))],
        [t["tdee"], str(analysis.get("tdee", 0))],
    ]
    tbl = _make_table(metrics, col_widths=[200, 200])
    c = colors.HexColor(risk_badge["color_hex"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary_dark"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor(COLORS["background_light"])),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (1, 2), (1, 2), c),
        ("TEXTCOLOR", (1, 2), (1, 2), colors.white),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 20))

    # Seccion: Alertas
    alerts_data = report_data.get("alerts", {})
    alerts_list = alerts_data.get("high", []) + alerts_data.get("medium", [])
    if alerts_list:
        elements.append(Paragraph(t["alerts"], t["_styles"]["subtitle"]))
        rows = [[t["type"], t["value"]]]
        for al in alerts_list[:6]:
            pbadge = format_alert_priority(al.get("priority", "low"), language)
            rows.append([f"[{pbadge['label']}] {al.get('type', '')}", al.get("message", "")])
        tbl_a = _make_table(rows, col_widths=[150, 350])
        elements.append(tbl_a)
        elements.append(Spacer(1, 20))

    # Seccion: Objetivos
    goals = report_data.get("goals", {})
    goals_list = goals.get("all", [])
    if goals_list:
        elements.append(Paragraph(t["objectives"], t["_styles"]["subtitle"]))
        for g in goals_list[:5]:
            elements.append(Paragraph(f"&#8226; {g}", t["_styles"]["normal"]))
        elements.append(Spacer(1, 20))

    # Seccion: Narrativas
    narratives = report_data.get("narratives", {})
    for nk in ["clinical_summary", "bmi_interpretation", "risk_interpretation"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))
            elements.append(Spacer(1, 10))

    # Seccion: ML + XAI
    ml = report_data.get("ml_prediction", {})
    if ml.get("available"):
        elements.append(Paragraph(t["ml_prediction"], t["_styles"]["subtitle"]))
        conf_badge = format_confidence_badge(ml.get("confidence", 0))
        ml_rows = [
            [t["metric"], t["value"]],
            ["Clasificacion", ml.get("predicted_class_label", "")],
            [t["confidence"], conf_badge["label"]],
            [t["model"], ml.get("model_used", "")],
        ]
        elements.append(_make_table(ml_rows, col_widths=[200, 200]))
        elements.append(Spacer(1, 15))

    xai = report_data.get("xai", {})
    if xai.get("available"):
        elements.append(Paragraph(t["xai_explanation"], t["_styles"]["subtitle"]))
        if xai.get("summary"):
            elements.append(Paragraph(xai["summary"], t["_styles"]["normal"]))
        if xai.get("main_reason"):
            elements.append(Paragraph(xai["main_reason"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 10))

    # Escenarios
    scenarios = format_scenarios(xai)
    if scenarios["has_scenarios"]:
        elements.append(Paragraph("Escenarios", t["_styles"]["subtitle"]))
        if scenarios["follow"]:
            sf = scenarios["follow"]
            elements.append(Paragraph(
                f"<b>{t['scenario_follow']}:</b> {sf.get('evolution_text', '')}",
                t["_styles"]["normal"],
            ))
        if scenarios["ignore"]:
            si = scenarios["ignore"]
            elements.append(Paragraph(
                f"<b>{t['scenario_ignore']}:</b> {si.get('risk_text', '')}",
                t["_styles"]["normal"],
            ))
        elements.append(Spacer(1, 15))

    # Seccion: Factores Clinicos
    profile = report_data.get("profile", {})
    chronic = profile.get("chronic_diseases", [])
    genetic = profile.get("genetic_risk_factors", [])
    if chronic or genetic:
        elements.append(Paragraph(t["clinical_factors"], t["_styles"]["subtitle"]))
        factors = [
            [t["type"], t["conditions"]],
            [t["chronic"], ", ".join(chronic) if chronic else t["no_data"]],
            [t["genetic"], ", ".join(genetic) if genetic else t["no_data"]],
        ]
        elements.append(_make_table(factors, col_widths=[150, 350]))
        elements.append(Spacer(1, 20))

    # Grafico
    if plot_bytes:
        elements.append(Paragraph(t["timeline"], t["_styles"]["subtitle"]))
        img = Image(io.BytesIO(plot_bytes))
        img.drawWidth = 6 * inch
        img.drawHeight = 3.5 * inch
        elements.append(img)

    doc.build(elements)
    buf.seek(0)
    return buf


# ==========================================
# PREDICTIONS REPORT PDF
# ==========================================

def generate_predictions_pdf(report_data, language="es"):
    t = get_translations(language)
    t["_styles"] = _get_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))

    elements.append(Paragraph(
        f"{t['app_name']} - {t['predictions_report']}", t["_styles"]["title"]
    ))
    elements.append(Paragraph(
        f"<b>{t['date_generated']}:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        t["_styles"]["normal"],
    ))
    if profile_info.get("display_name"):
        elements.append(Paragraph(
            f"<b>{t['patient']}:</b> {profile_info['display_name']}",
            t["_styles"]["normal"],
        ))
    elements.append(Spacer(1, 20))

    # Proyecciones de peso
    wp = format_weight_projection(report_data.get("predictions"))
    if wp.get("available"):
        elements.append(Paragraph(t["weight_summary"], t["_styles"]["subtitle"]))
        rows = [[t["period"], t["weight"]]]
        for p in wp["periods"]:
            rows.append([p["label"], f"{p['weight_kg']} kg"])
        elements.append(_make_table(rows, col_widths=[200, 200]))
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph(t["weight_summary"], t["_styles"]["subtitle"]))
        elements.append(Paragraph("No hay datos de proyeccion disponibles.", t["_styles"]["normal"]))
        elements.append(Spacer(1, 20))

    # ML
    ml = report_data.get("ml_prediction", {})
    if ml.get("available"):
        elements.append(Paragraph(t["ml_prediction"], t["_styles"]["subtitle"]))
        conf = format_confidence_badge(ml.get("confidence", 0))
        rows = [
            [t["metric"], t["value"]],
            ["Clasificacion", ml.get("predicted_class_label", "")],
            [t["confidence"], conf["label"]],
            [t["model"], ml.get("model_used", "")],
        ]
        elements.append(_make_table(rows, col_widths=[200, 200]))
        elements.append(Spacer(1, 15))

    # XAI
    xai = report_data.get("xai", {})
    if xai.get("available"):
        elements.append(Paragraph(t["xai_explanation"], t["_styles"]["subtitle"]))
        if xai.get("summary"):
            elements.append(Paragraph(xai["summary"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 10))

    # Narrativas
    narratives = report_data.get("narratives", {})
    for nk in ["ml_interpretation", "prognosis"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))
            elements.append(Spacer(1, 10))

    # Escenarios
    scenarios = format_scenarios(xai)
    if scenarios["has_scenarios"]:
        elements.append(Paragraph("Escenarios", t["_styles"]["subtitle"]))
        if scenarios["follow"]:
            sf = scenarios["follow"]
            elements.append(Paragraph(
                f"<b>{t['scenario_follow']}:</b> Peso proyectado: "
                f"{sf.get('projected_weight_kg', '')} kg. "
                f"{sf.get('evolution_text', '')}",
                t["_styles"]["normal"],
            ))
        if scenarios["ignore"]:
            si = scenarios["ignore"]
            elements.append(Paragraph(
                f"<b>{t['scenario_ignore']}:</b> Peso proyectado: "
                f"{si.get('projected_weight_kg', '')} kg. "
                f"{si.get('risk_text', '')}",
                t["_styles"]["normal"],
            ))

    doc.build(elements)
    buf.seek(0)
    return buf


# ==========================================
# NUTRITION REPORT PDF
# ==========================================

def generate_nutrition_pdf(report_data, language="es"):
    t = get_translations(language)
    t["_styles"] = _get_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))

    elements.append(Paragraph(
        f"{t['app_name']} - {t['recipes_report']}", t["_styles"]["title"]
    ))
    elements.append(Paragraph(
        f"<b>{t['date_generated']}:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        t["_styles"]["normal"],
    ))
    if profile_info.get("display_name"):
        elements.append(Paragraph(
            f"<b>{t['patient']}:</b> {profile_info['display_name']}",
            t["_styles"]["normal"],
        ))
    elements.append(Spacer(1, 20))

    # Resumen nutricional
    elements.append(Paragraph(t["nutrition_summary"], t["_styles"]["subtitle"]))
    macros = format_macronutrients(report_data.get("nutrition"))
    if macros.get("available"):
        rows = [
            [t["metric"], t["value"]],
            [t["daily_calories"], f"{macros['daily_calories']} kcal"],
            [t["protein"], f"{macros['protein_g']} g ({macros['protein_pct']}%)"],
            [t["carbs"], f"{macros['carbs_g']} g ({macros['carbs_pct']}%)"],
            [t["fats"], f"{macros['fats_g']} g ({macros['fats_pct']}%)"],
        ]
        elements.append(_make_table(rows, col_widths=[200, 200]))
        elements.append(Spacer(1, 20))

        # Recetas sugeridas
        elements.append(Paragraph(t["suggested_recipes"], t["_styles"]["subtitle"]))
        protein = macros["protein_g"]
        recipes = [
            [t["meal"], t["recipe"], t["protein_g"]],
            [t["breakfast"],
             "Avena con frutas frescas, chia y un punado de nueces" if language == "es"
             else "Oatmeal with fresh fruits, chia and a handful of nuts",
             str(round(protein * 0.2))],
            [t["lunch"],
             "Pechuga de pollo a la plancha con quinoa y mix de vegetales" if language == "es"
             else "Grilled chicken breast with quinoa and mixed vegetables",
             str(round(protein * 0.4))],
            [t["dinner"],
             "Ensalada ligera de salmon fresco, aguacate y espinaca" if language == "es"
             else "Light salad with fresh salmon, avocado and spinach",
             str(round(protein * 0.3))],
            [t["snack"],
             "Un yogur griego natural o un punado de almendras tostadas" if language == "es"
             else "A natural Greek yogurt or a handful of roasted almonds",
             str(round(protein * 0.1))],
        ]
        elements.append(_make_table(recipes, col_widths=[100, 250, 100]))
    else:
        elements.append(Paragraph(t["no_data"], t["_styles"]["normal"]))

    # Narrativas
    narratives = report_data.get("narratives", {})
    for nk in ["recommendations_summary"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))

    doc.build(elements)
    buf.seek(0)
    return buf


# ==========================================
# EXERCISE REPORT PDF
# ==========================================

def generate_exercise_pdf(report_data, language="es"):
    t = get_translations(language)
    t["_styles"] = _get_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))

    elements.append(Paragraph(
        f"{t['app_name']} - {t['exercise_report']}", t["_styles"]["title"]
    ))
    elements.append(Paragraph(
        f"<b>{t['date_generated']}:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        t["_styles"]["normal"],
    ))
    if profile_info.get("display_name"):
        elements.append(Paragraph(
            f"<b>{t['patient']}:</b> {profile_info['display_name']}",
            t["_styles"]["normal"],
        ))
    elements.append(Spacer(1, 20))

    # Plan de ejercicio
    elements.append(Paragraph(t["exercise_plan"], t["_styles"]["subtitle"]))
    ex = format_exercise_plan(report_data.get("exercise"))
    if ex.get("available"):
        rows = [
            [t["type"], t["duration"]],
            [t["cardio"], ex["cardio"]],
            [t["strength"], ex["strength"]],
            [t["flexibility"], ex["flexibility"]],
        ]
        elements.append(_make_table(rows, col_widths=[200, 200]))
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph(t["no_data"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 20))

    # Narrativas
    narratives = report_data.get("narratives", {})
    for nk in ["risk_interpretation", "recommendations_summary"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))
            elements.append(Spacer(1, 10))

    doc.build(elements)
    buf.seek(0)
    return buf
