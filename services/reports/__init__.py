"""
services.reports — Package de reportes inteligentes.

API unica para:
- ReportEngine (capa de datos)
- Renderers PDF, Excel, Word (capa de presentacion)
"""

from services.reports.report_engine import ReportEngine
from services.reports.pdf_renderer import (
    generate_health_pdf,
    generate_predictions_pdf,
    generate_nutrition_pdf,
    generate_exercise_pdf,
)
from services.reports.excel_renderer import (
    generate_health_excel,
    generate_predictions_excel,
    generate_nutrition_excel,
    generate_exercise_excel,
)
from services.reports.word_renderer import (
    generate_health_word,
    generate_predictions_word,
    generate_nutrition_word,
    generate_exercise_word,
)

__all__ = [
    "ReportEngine",
    "generate_health_pdf", "generate_predictions_pdf",
    "generate_nutrition_pdf", "generate_exercise_pdf",
    "generate_health_excel", "generate_predictions_excel",
    "generate_nutrition_excel", "generate_exercise_excel",
    "generate_health_word", "generate_predictions_word",
    "generate_nutrition_word", "generate_exercise_word",
]
