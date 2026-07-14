"""
advanced_reports.py — Wrapper de compatibilidad.

Delega todo el renderizado a backend/services/reports/.
Mantenido temporalmente para compatibilidad con imports existentes.

FLUJO:
  from advanced_reports import generate_risk_report_pdf
  -> delega a services.reports.pdf_renderer.generate_health_pdf
"""

from services.reports.report_engine import ReportEngine
from services.reports.pdf_renderer import (
    generate_health_pdf as _generate_health_pdf,
    generate_predictions_pdf as _generate_predictions_pdf,
    generate_nutrition_pdf as _generate_nutrition_pdf,
    generate_exercise_pdf as _generate_exercise_pdf,
)
from services.reports.excel_renderer import (
    generate_health_excel as _generate_health_excel,
    generate_predictions_excel as _generate_predictions_excel,
    generate_nutrition_excel as _generate_nutrition_excel,
    generate_exercise_excel as _generate_exercise_excel,
)
from services.reports.word_renderer import (
    generate_health_word as _generate_health_word,
    generate_predictions_word as _generate_predictions_word,
    generate_nutrition_word as _generate_nutrition_word,
    generate_exercise_word as _generate_exercise_word,
)
from services.reports.styles import get_translations, get_risk_colors


def _build_report_data(analysis_data, profile_data, predictions_data=None, history_data=None):
    """Convierte formato legacy a report_data via ReportEngine."""
    engine = ReportEngine()
    return engine.build_from_db(
        profile=profile_data,
        analysis=analysis_data,
        predictions=predictions_data,
        history=history_data,
    )


# ==========================================
# WRAPPERS — HEALTH (Risk Report)
# ==========================================

def generate_risk_report_pdf(analysis_data, profile_data, score_history=None,
                             plot_bytes=None, language="es"):
    report = _build_report_data(analysis_data, profile_data,
                                history_data=score_history)
    return _generate_health_pdf(report, plot_bytes=plot_bytes, language=language)


def generate_risk_report_excel(analysis_data, profile_data, history_data=None,
                               language="es"):
    report = _build_report_data(analysis_data, profile_data,
                                history_data=history_data)
    return _generate_health_excel(report, language=language)


def generate_risk_report_word(analysis_data, profile_data, plot_bytes=None,
                              language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_health_word(report, plot_bytes=plot_bytes, language=language)


# ==========================================
# WRAPPERS — PREDICTIONS
# ==========================================

def generate_predictions_report_pdf(analysis_data, profile_data,
                                    latest_prediction=None, language="es"):
    report = _build_report_data(analysis_data, profile_data,
                                predictions_data=latest_prediction)
    return _generate_predictions_pdf(report, language=language)


def generate_predictions_report_excel(analysis_data, profile_data,
                                      latest_prediction=None, language="es"):
    report = _build_report_data(analysis_data, profile_data,
                                predictions_data=latest_prediction)
    return _generate_predictions_excel(report, language=language)


def generate_predictions_report_word(analysis_data, profile_data,
                                     latest_prediction=None, language="es"):
    report = _build_report_data(analysis_data, profile_data,
                                predictions_data=latest_prediction)
    return _generate_predictions_word(report, language=language)


# ==========================================
# WRAPPERS — RECIPES (Nutrition)
# ==========================================

def generate_recipes_report_pdf(analysis_data, profile_data, language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_nutrition_pdf(report, language=language)


def generate_recipes_report_excel(analysis_data, profile_data, language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_nutrition_excel(report, language=language)


def generate_recipes_report_word(analysis_data, profile_data, language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_nutrition_word(report, language=language)


# ==========================================
# WRAPPERS — EXERCISE
# ==========================================

def generate_exercise_report_pdf(analysis_data, profile_data, language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_exercise_pdf(report, language=language)


def generate_exercise_report_excel(analysis_data, profile_data, language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_exercise_excel(report, language=language)


def generate_exercise_report_word(analysis_data, profile_data, language="es"):
    report = _build_report_data(analysis_data, profile_data)
    return _generate_exercise_word(report, language=language)
