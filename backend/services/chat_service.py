import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ChatService:
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
        self._client = None
        self._groq_available = False
        self._init_client()

    def _init_client(self):
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            logger.warning("GROQ_API_KEY not set — AI chat disabled")
            return
        try:
            from groq import Groq
            self._client = Groq(api_key=api_key)
            self._groq_available = True
            logger.info("Groq client initialized")
        except ImportError:
            logger.warning("groq package not installed — AI chat disabled")
        except Exception as e:
            logger.error(f"Groq init failed: {e}")

    @property
    def is_available(self) -> bool:
        return self._groq_available and self._client is not None

    def _build_system_prompt(self, language: str = "es") -> str:
        if language == "en":
            return (
                "You are Health AI Assistant, a professional health education chatbot.\n\n"
                "ROLE:\n"
                "- Provide clear, educational explanations about the user's health data.\n"
                "- Help the user understand their health score, BMI, alerts, predictions, and AI explanations.\n"
                "- Offer general wellness guidance based on the data provided.\n\n"
                "SAFETY RULES (NON-NEGOTIABLE):\n"
                "- NEVER diagnose diseases or medical conditions.\n"
                "- NEVER replace a medical professional's judgment.\n"
                "- NEVER prescribe medications or treatments.\n"
                "- NEVER issue emergency medical advice.\n"
                "- ALWAYS recommend consulting a healthcare professional for specific concerns.\n"
                "- ALWAYS include a disclaimer when giving health-related information.\n\n"
                "RESPONSE FORMAT:\n"
                "- Be professional, educational, and easy to understand.\n"
                "- Use plain language, avoid unnecessary jargon.\n"
                "- Keep responses concise (2-4 paragraphs max).\n"
                "- If you don't have enough data, say so honestly.\n\n"
                "DISCLAIMER:\n"
                "Append at the end of every response:\n"
                "\"This information is educational only and does not replace medical advice. "
                "Consult a healthcare professional for personalized guidance.\""
            )
        return (
            "Eres el Asistente de Salud Health AI, un chatbot educativo profesional.\n\n"
            "ROL:\n"
            "- Proporciona explicaciones claras y educativas sobre los datos de salud del usuario.\n"
            "- Ayuda al usuario a entender su puntuación de salud, IMC, alertas, predicciones y explicaciones de IA.\n"
            "- Ofrece orientación general de bienestar basada en los datos proporcionados.\n\n"
            "REGLAS DE SEGURIDAD (INNEGOCIABLES):\n"
            "- NUNCA diagnostiques enfermedades o condiciones médicas.\n"
            "- NUNCA reemplaces el juicio de un profesional médico.\n"
            "- NUNCA recetes medicamentos ni tratamientos.\n"
            "- NUNCA emitas consejos de emergencia médica.\n"
            "- SIEMPRE recomienda consultar a un profesional de la salud para preocupaciones específicas.\n"
            "- SIEMPRE incluye un descrito al dar información relacionada con la salud.\n\n"
            "FORMATO DE RESPUESTA:\n"
            "- Sé profesional, educativo y fácil de entender.\n"
            "- Usa lenguaje claro, evita jerga innecesaria.\n"
            "- Respuestas concisas (máximo 2-4 párrafos).\n"
            "- Si no tienes suficientes datos, dilo honestamente.\n\n"
            "DESCRITO LEGAL:\n"
            "Al final de cada respuesta agrega:\n"
            "\"Esta información es solo educativa y no reemplaza el consejo médico. "
            "Consulta a un profesional de la salud para orientación personalizada.\""
        )

    def _build_user_context(
        self,
        message: str,
        analysis: Optional[Dict] = None,
        prediction: Optional[Dict] = None,
        xai: Optional[Dict] = None,
        language: str = "es"
    ) -> str:
        sections = []

        if language == "en":
            sections.append("PATIENT HEALTH DATA:")
        else:
            sections.append("DATOS DE SALUD DEL PACIENTE:")

        if analysis:
            score = analysis.get("health_score", "N/A")
            bmi = analysis.get("bmi", "N/A")
            bmi_cat = analysis.get("bmi_category", "N/A")
            tdee = analysis.get("tdee", "N/A")
            alerts = analysis.get("alerts", [])
            goals = analysis.get("weekly_goals", [])

            if language == "en":
                sections.append(f"Health Score: {score}/100")
                sections.append(f"BMI: {bmi} ({bmi_cat})")
                sections.append(f"TDEE: {tdee} kcal/day")
            else:
                sections.append(f"Puntuación de Salud: {score}/100")
                sections.append(f"IMC: {bmi} ({bmi_cat})")
                sections.append(f"TDEE: {tdee} kcal/día")

            if alerts:
                alert_texts = [a.get("message", str(a)) if isinstance(a, dict) else str(a) for a in alerts]
                if language == "en":
                    sections.append(f"Alerts: {'; '.join(alert_texts)}")
                else:
                    sections.append(f"Alertas: {'; '.join(alert_texts)}")

            if goals:
                if language == "en":
                    sections.append(f"Weekly Goals: {'; '.join(goals[:5])}")
                else:
                    sections.append(f"Objetivos Semanales: {'; '.join(goals[:5])}")

            nutrition = (analysis.get("health_plan") or {}).get("nutrition") or {}
            if nutrition:
                cal = nutrition.get("daily_calories", "N/A")
                macro = nutrition.get("macronutrients") or {}
                if language == "en":
                    sections.append(f"Daily Calories: {cal} kcal | Protein: {macro.get('protein','?')}g | Carbs: {macro.get('carbs','?')}g | Fats: {macro.get('fats','?')}g")
                else:
                    sections.append(f"Calorías Diarias: {cal} kcal | Proteína: {macro.get('protein','?')}g | Carbohidratos: {macro.get('carbs','?')}g | Grasas: {macro.get('fats','?')}g")

        if prediction:
            pred_class = prediction.get("predicted_class") or prediction.get("predictedCategory", "N/A")
            confidence = prediction.get("confidence", "N/A")
            model = prediction.get("model_used", "N/A")
            if language == "en":
                sections.append(f"\nML Prediction: {pred_class} (Confidence: {confidence}%, Model: {model})")
            else:
                sections.append(f"\nPredicción ML: {pred_class} (Confianza: {confidence}%, Modelo: {model})")

        if xai:
            summary = xai.get("summary", "")
            main_reason = xai.get("main_reason", "")
            confidence_text = xai.get("confidence_text", "")
            risk = xai.get("risk_explanation", "")
            features = xai.get("important_features", [])

            if summary or main_reason:
                if language == "en":
                    sections.append(f"\nAI Explanation:")
                    if summary:
                        sections.append(f"  Summary: {summary}")
                    if main_reason:
                        sections.append(f"  Main Reason: {main_reason}")
                    if confidence_text:
                        sections.append(f"  Confidence: {confidence_text}")
                    if risk:
                        sections.append(f"  Risk: {risk}")
                else:
                    sections.append(f"\nExplicación de IA:")
                    if summary:
                        sections.append(f"  Resumen: {summary}")
                    if main_reason:
                        sections.append(f"  Razón Principal: {main_reason}")
                    if confidence_text:
                        sections.append(f"  Confianza: {confidence_text}")
                    if risk:
                        sections.append(f"  Riesgo: {risk}")

            if features:
                feat_list = [f.get("display_name", f.get("name", "?")) for f in features[:5]]
                if language == "en":
                    sections.append(f"  Key Factors: {', '.join(feat_list)}")
                else:
                    sections.append(f"  Factores Clave: {', '.join(feat_list)}")

            scenario_follow = xai.get("scenario_follow")
            scenario_ignore = xai.get("scenario_ignore")
            if scenario_follow:
                pw = scenario_follow.get("projected_weight_kg", "?")
                cat = scenario_follow.get("projected_category", "?")
                if language == "en":
                    sections.append(f"  Follow Plan: → {pw}kg, category: {cat}")
                else:
                    sections.append(f"  Seguir Plan: → {pw}kg, categoría: {cat}")
            if scenario_ignore:
                pw = scenario_ignore.get("projected_weight_kg", "?")
                cat = scenario_ignore.get("projected_category", "?")
                if language == "en":
                    sections.append(f"  Ignore Plan: → {pw}kg, category: {cat}")
                else:
                    sections.append(f"  Ignorar Plan: → {pw}kg, categoría: {cat}")

        sections.append("")
        if language == "en":
            sections.append(f"USER QUESTION: {message}")
        else:
            sections.append(f"PREGUNTA DEL USUARIO: {message}")

        return "\n".join(sections)

    def chat(
        self,
        message: str,
        language: str = "es",
        analysis: Optional[Dict] = None,
        prediction: Optional[Dict] = None,
        xai: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "success": False,
                "response": (
                    "AI service is not available. Configure GROQ_API_KEY to enable it."
                    if language == "en"
                    else "El servicio de IA no está disponible. Configura GROQ_API_KEY para habilitarlo."
                ),
                "source": "unavailable"
            }

        system_prompt = self._build_system_prompt(language)
        user_context = self._build_user_context(message, analysis, prediction, xai, language)

        try:
            chat_completion = self._client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ],
                temperature=0.3,
                max_tokens=1024,
                top_p=0.9,
            )

            response_text = chat_completion.choices[0].message.content.strip()

            return {
                "success": True,
                "response": response_text,
                "source": "groq"
            }

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return {
                "success": False,
                "response": (
                    f"I couldn't process your question right now. Please try again later.\n\nTechnical detail: {str(e)[:200]}"
                    if language == "en"
                    else f"No pude procesar tu pregunta en este momento. Intenta de nuevo más tarde.\n\nDetalle técnico: {str(e)[:200]}"
                ),
                "source": "error"
            }


chat_service = ChatService()
