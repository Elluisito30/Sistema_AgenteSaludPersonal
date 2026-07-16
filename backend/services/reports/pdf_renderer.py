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
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Circle, Rect, String

from services.reports.styles import get_translations, COLORS
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
            "MainTitle", parent=base["Heading1"], fontSize=16,
            spaceAfter=6, textColor=colors.white,
            alignment=1, fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "SubTitle", parent=base["Heading2"], fontSize=13,
            spaceAfter=10, spaceBefore=4,
            textColor=colors.HexColor(COLORS["primary_dark"]),
            fontName="Helvetica-Bold",
        ),
        "normal": ParagraphStyle(
            "BodyNormal", parent=base["Normal"], fontSize=10,
            textColor=colors.HexColor(COLORS["text_dark"]),
            leading=14,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"], fontSize=9,
            textColor=colors.HexColor(COLORS["text_light"]),
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", parent=base["Heading3"], fontSize=11,
            spaceAfter=6, spaceBefore=12,
            textColor=colors.HexColor(COLORS["primary_medium"]),
            fontName="Helvetica-Bold",
        ),
        "banner_meta": ParagraphStyle(
            "BannerMeta", parent=base["Normal"], fontSize=9,
            textColor=colors.HexColor("#dfe6e9"), alignment=1,
        ),
    }


def _soft_table_style(extra=None):
    """Estilo de tabla suave: sin grid negro duro, padding amplio."""
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary_dark"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor(COLORS["background_soft"])),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(COLORS["text_dark"])),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(COLORS["primary_accent"])),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, colors.HexColor(COLORS["grid_soft"])),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(COLORS["grid_soft"])),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.HexColor(COLORS["background_soft"]),
            colors.HexColor(COLORS["white"]),
        ]),
    ]
    if extra:
        style.extend(extra)
    return TableStyle(style)


def _make_table(data, col_widths=None, extra_style=None):
    t = Table(data, colWidths=col_widths)
    t.setStyle(_soft_table_style(extra_style))
    return t


def _header_banner(elements, t, profile_info, report_title_key="health_report"):
    """Banner de cabecera coloreado con nombre de la app."""
    styles = t["_styles"]
    app_line = Paragraph(f"{t['app_name']}", styles["title"])
    report_line = Paragraph(t.get(report_title_key, t["health_report"]), styles["banner_meta"])
    meta_parts = [
        f"{t['date_generated']}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ]
    if profile_info.get("display_name"):
        meta_parts.append(f"{t['patient']}: {profile_info['display_name']}")
    meta_line = Paragraph("  ·  ".join(meta_parts), styles["banner_meta"])

    banner = Table(
        [[app_line], [report_line], [meta_line]],
        colWidths=[460],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLORS["primary_dark"])),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("LINEBELOW", (0, -1), (-1, -1), 3, colors.HexColor(COLORS["primary_accent"])),
    ]))
    elements.append(banner)
    elements.append(Spacer(1, 18))


def _health_score_drawing(score, size=90):
    """Dibujo circular simple del health score (0-100)."""
    try:
        score = float(score or 0)
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    if score >= 80:
        fill = COLORS["success"]
    elif score >= 60:
        fill = COLORS["info"]
    elif score >= 40:
        fill = COLORS["warning"]
    else:
        fill = COLORS["danger"]

    d = Drawing(size + 20, size + 10)
    cx, cy = (size + 20) / 2, (size + 10) / 2
    radius = size / 2 - 4

    # Anillo de fondo
    d.add(Circle(cx, cy, radius, fillColor=colors.HexColor(COLORS["background_light"]),
                 strokeColor=colors.HexColor(COLORS["grid_soft"]), strokeWidth=1.5))
    # Circulo interior coloreado
    inner_r = radius * 0.72
    d.add(Circle(cx, cy, inner_r, fillColor=colors.HexColor(fill),
                 strokeColor=None, strokeWidth=0))
    # Barra de progreso inferior como refuerzo visual
    bar_w = size * 0.85
    bar_h = 5
    bar_x = cx - bar_w / 2
    bar_y = 4
    d.add(Rect(bar_x, bar_y, bar_w, bar_h, fillColor=colors.HexColor(COLORS["grid_soft"]),
               strokeColor=None, strokeWidth=0))
    d.add(Rect(bar_x, bar_y, bar_w * (score / 100.0), bar_h,
               fillColor=colors.HexColor(fill), strokeColor=None, strokeWidth=0))
    # Texto del score
    d.add(String(cx, cy - 4, f"{int(score)}", fontSize=18, fillColor=colors.white,
                 textAnchor="middle", fontName="Helvetica-Bold"))
    return d


# ==========================================
# HEALTH REPORT PDF
# ==========================================

def generate_health_pdf(report_data, plot_bytes=None, language="es"):
    t = get_translations(language)
    t["_styles"] = _get_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=40, leftMargin=40,
                            topMargin=36, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))
    _header_banner(elements, t, profile_info, "health_report")

    analysis = report_data.get("analysis", {})
    risk_badge = format_risk_badge(analysis.get("health_risk"), language)
    bmi_ind = format_bmi_indicator(
        analysis.get("bmi"), analysis.get("bmi_category"), language
    )

    elements.append(Paragraph(t["risk_evaluation"], t["_styles"]["subtitle"]))

    # Visual del health score + metricas
    score = analysis.get("health_score", 0)
    score_draw = _health_score_drawing(score)
    metrics = [
        [t["metric"], t["value"]],
        [t["health_score"], f"{score} / 100"],
        [t["clinical_status"], risk_badge["label"]],
        [t["bmi"], f"{bmi_ind['value']} ({bmi_ind['label']})"],
        [t["bmr"], str(analysis.get("bmr", 0))],
        [t["tdee"], str(analysis.get("tdee", 0))],
    ]
    metrics_tbl = _make_table(metrics, col_widths=[160, 160], extra_style=[
        ("BACKGROUND", (1, 2), (1, 2), colors.HexColor(risk_badge["color_hex"])),
        ("TEXTCOLOR", (1, 2), (1, 2), colors.white),
        ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
    ])

    layout = Table(
        [[score_draw, metrics_tbl]],
        colWidths=[120, 340],
    )
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(layout)
    elements.append(Spacer(1, 18))

    # Alertas
    alerts_data = report_data.get("alerts", {})
    alerts_list = alerts_data.get("high", []) + alerts_data.get("medium", [])
    if alerts_list:
        elements.append(Paragraph(t["alerts"], t["_styles"]["subtitle"]))
        rows = [[t["type"], t["value"]]]
        for al in alerts_list[:6]:
            pbadge = format_alert_priority(al.get("priority", "low"), language)
            rows.append([f"[{pbadge['label']}] {al.get('type', '')}", al.get("message", "")])
        elements.append(_make_table(rows, col_widths=[150, 310]))
        elements.append(Spacer(1, 16))

    # Objetivos
    goals = report_data.get("goals", {})
    goals_list = goals.get("all", [])
    if goals_list:
        elements.append(Paragraph(t["objectives"], t["_styles"]["subtitle"]))
        for g in goals_list[:5]:
            elements.append(Paragraph(f"&#8226; {g}", t["_styles"]["normal"]))
        elements.append(Spacer(1, 16))

    # Narrativas
    narratives = report_data.get("narratives", {})
    for nk in ["clinical_summary", "bmi_interpretation", "risk_interpretation"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))
            elements.append(Spacer(1, 8))

    # ML + XAI
    ml = report_data.get("ml_prediction", {})
    if ml.get("available"):
        elements.append(Paragraph(t["ml_prediction"], t["_styles"]["subtitle"]))
        conf_badge = format_confidence_badge(ml.get("confidence", 0), language)
        ml_rows = [
            [t["metric"], t["value"]],
            [t["classification"], ml.get("predicted_class_label", "")],
            [t["confidence"], f"{conf_badge['label']} ({conf_badge['level']})"],
            [t["model"], ml.get("model_used", "")],
        ]
        elements.append(_make_table(ml_rows, col_widths=[200, 260]))
        elements.append(Spacer(1, 14))

    xai = report_data.get("xai", {})
    if xai.get("available"):
        elements.append(Paragraph(t["xai_explanation"], t["_styles"]["subtitle"]))
        if xai.get("summary"):
            elements.append(Paragraph(xai["summary"], t["_styles"]["normal"]))
        if xai.get("main_reason"):
            elements.append(Paragraph(xai["main_reason"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 10))

    scenarios = format_scenarios(xai)
    if scenarios["has_scenarios"]:
        elements.append(Paragraph(t["scenarios"], t["_styles"]["subtitle"]))
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
        elements.append(Spacer(1, 14))

    # Factores clinicos
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
        elements.append(_make_table(factors, col_widths=[150, 310]))
        elements.append(Spacer(1, 16))

    # Grafico
    if plot_bytes:
        from reportlab.platypus import Image
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
                            topMargin=36, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))
    _header_banner(elements, t, profile_info, "predictions_report")

    wp = format_weight_projection(report_data.get("predictions"))
    if wp.get("available"):
        elements.append(Paragraph(t["weight_summary"], t["_styles"]["subtitle"]))
        rows = [[t["period"], t["weight"]]]
        for p in wp["periods"]:
            rows.append([p["label"], f"{p['weight_kg']} kg"])
        elements.append(_make_table(rows, col_widths=[200, 260]))
        elements.append(Spacer(1, 16))
    else:
        elements.append(Paragraph(t["weight_summary"], t["_styles"]["subtitle"]))
        elements.append(Paragraph(t["no_projection_data"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 16))

    ml = report_data.get("ml_prediction", {})
    if ml.get("available"):
        elements.append(Paragraph(t["ml_prediction"], t["_styles"]["subtitle"]))
        conf = format_confidence_badge(ml.get("confidence", 0), language)
        rows = [
            [t["metric"], t["value"]],
            [t["classification"], ml.get("predicted_class_label", "")],
            [t["confidence"], f"{conf['label']} ({conf['level']})"],
            [t["model"], ml.get("model_used", "")],
        ]
        elements.append(_make_table(rows, col_widths=[200, 260]))
        elements.append(Spacer(1, 14))

    xai = report_data.get("xai", {})
    if xai.get("available"):
        elements.append(Paragraph(t["xai_explanation"], t["_styles"]["subtitle"]))
        if xai.get("summary"):
            elements.append(Paragraph(xai["summary"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 10))

    narratives = report_data.get("narratives", {})
    for nk in ["ml_interpretation", "prognosis"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))
            elements.append(Spacer(1, 8))

    scenarios = format_scenarios(xai)
    if scenarios["has_scenarios"]:
        elements.append(Paragraph(t["scenarios"], t["_styles"]["subtitle"]))
        if scenarios["follow"]:
            sf = scenarios["follow"]
            elements.append(Paragraph(
                f"<b>{t['scenario_follow']}:</b> {t['projected_weight_label']}: "
                f"{sf.get('projected_weight_kg', '')} kg. "
                f"{sf.get('evolution_text', '')}",
                t["_styles"]["normal"],
            ))
        if scenarios["ignore"]:
            si = scenarios["ignore"]
            elements.append(Paragraph(
                f"<b>{t['scenario_ignore']}:</b> {t['projected_weight_label']}: "
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
                            topMargin=36, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))
    _header_banner(elements, t, profile_info, "recipes_report")

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
        elements.append(_make_table(rows, col_widths=[200, 260]))
        elements.append(Spacer(1, 16))

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
        elements.append(_make_table(recipes, col_widths=[100, 250, 110]))
    else:
        elements.append(Paragraph(t["no_data"], t["_styles"]["normal"]))

    narratives = report_data.get("narratives", {})
    for nk in ["recommendations_summary"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Spacer(1, 14))
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
                            topMargin=36, bottomMargin=40)
    elements = []
    profile_info = format_profile_summary(report_data.get("profile"))
    _header_banner(elements, t, profile_info, "exercise_report")

    elements.append(Paragraph(t["exercise_plan"], t["_styles"]["subtitle"]))
    ex = format_exercise_plan(report_data.get("exercise"))
    if ex.get("available"):
        rows = [
            [t["type"], t["duration"]],
            [t["cardio"], ex["cardio"]],
            [t["strength"], ex["strength"]],
            [t["flexibility"], ex["flexibility"]],
        ]
        elements.append(_make_table(rows, col_widths=[200, 260]))
        elements.append(Spacer(1, 16))
    else:
        elements.append(Paragraph(t["no_data"], t["_styles"]["normal"]))
        elements.append(Spacer(1, 16))

    narratives = report_data.get("narratives", {})
    for nk in ["risk_interpretation", "recommendations_summary"]:
        nav = narratives.get(nk)
        if nav and nav.get("text"):
            elements.append(Paragraph(nav["title"], t["_styles"]["section_title"]))
            elements.append(Paragraph(nav["text"], t["_styles"]["normal"]))
            elements.append(Spacer(1, 8))

    doc.build(elements)
    buf.seek(0)
    return buf
