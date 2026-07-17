import os
import logging
from typing import Optional, Dict, Any, List

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
                "You are Health AI — a warm, conversational health assistant. Think ChatGPT, not a medical dashboard.\n\n"
                "HOW YOU WORK:\n"
                "- You have access to the last 15 messages. Use them to maintain full conversational context.\n"
                "- If the user says \"that\", \"the other thing\", \"my brother\", \"if I exercise\" — resolve the reference from conversation history.\n"
                "- NEVER re-explain the user's score, BMI, or alerts unless they ask again. They know their numbers.\n"
                "- Answer ONLY what is asked. If they ask about food, talk about food — not exercise, not sleep.\n"
                "- Keep responses to 1-3 short paragraphs. Prefer brevity.\n"
                "- Use natural, everyday language. No jargon unless the user uses it first.\n"
                "- Never say \"According to your clinical data...\" or \"Based on your health profile...\" — just answer naturally.\n"
                "- If greeted, respond warmly and briefly. Do NOT analyze health data.\n"
                "- You have the patient's health data below. Use it ONLY when directly relevant.\n"
                "- Give practical, actionable advice: \"try adding a handful of nuts as a snack\" not \"eat better\".\n"
                "- If the question is vague, ask for clarification instead of guessing.\n"
                "- Tailor responses to the user's specific data when relevant.\n\n"
                "SAFETY (NON-NEGOTIABLE):\n"
                "- NEVER diagnose conditions or prescribe medications.\n"
                "- NEVER give emergency advice — tell them to seek immediate medical help.\n"
                "- When relevant, briefly note your info is educational, not a substitute for professional medical advice."
            )
        return (
            "Eres Health AI — un asistente de salud conversacional y cálido. Piensa en ChatGPT, no en un panel médico.\n\n"
            "CÓMO FUNCIONAS:\n"
            "- Tienes acceso a los últimos 15 mensajes. Úsalos para mantener el contexto conversacional completo.\n"
            "- Si el usuario dice \"eso\", \"lo otro\", \"mi hermano\", \"si hago ejercicio\" — resuelve la referencia del historial.\n"
            "- NUNCA vuelvas a explicar la puntuación, el IMC o las alertas a menos que lo pregunten de nuevo. Ya lo saben.\n"
            "- Responde SOLO lo que preguntan. Si pregunta sobre comida, habla de comida — no de ejercicio ni sueño.\n"
            "- Respuestas de 1-3 párrafos cortos. Prefiere la brevedad.\n"
            "- Lenguaje natural y cotidiano. Sin jerga médica a menos que el usuario la use primero.\n"
            "- Nunca digas \"De acuerdo con tus datos clínicos...\" o \"Basándome en tu perfil...\" — simplemente responde.\n"
            "- Si te saludan, responde cálidamente y breve. NO analices datos de salud.\n"
            "- Tienes los datos del paciente más abajo. Úsalos SOLO cuando sean directamente relevantes.\n"
            "- Da consejos prácticos y accionables: \"intenta agregar un puñado de nueces como snack\" no \"come mejor\".\n"
            "- Si la pregunta es vaga, pide clarificación en vez de adivinar.\n"
            "- Adapta las respuestas a los datos específicos del usuario cuando sea relevante.\n\n"
            "SEGURIDAD (INNEGOCIABLE):\n"
            "- NUNCA diagnostiques enfermedades ni recetes medicamentos.\n"
            "- NUNCA des consejos de emergencia — indica que busque atención médica inmediata.\n"
            "- Cuando sea relevante, menciona brevemente que tu información es educativa y no sustituye el consejo médico profesional."
        )

    def _build_user_context(
        self,
        message: str,
        analysis: Optional[Dict] = None,
        prediction: Optional[Dict] = None,
        xai: Optional[Dict] = None,
        language: str = "es",
        diary: Optional[Dict] = None,
    ) -> str:
        sections = []

        if language == "en":
            sections.append("PATIENT HEALTH DATA (use only when directly relevant — do NOT repeat in every response):")
        else:
            sections.append("DATOS DE SALUD DEL PACIENTE (usa solo cuando sea relevante — NO repitas en cada respuesta):")

        if analysis:
            score = analysis.get("health_score", "N/A")
            bmi = analysis.get("bmi", "N/A")
            bmi_cat = analysis.get("bmi_category", "N/A")
            alerts = analysis.get("alerts", [])

            if language == "en":
                sections.append(f"Score: {score}/100 | BMI: {bmi} ({bmi_cat})")
            else:
                sections.append(f"Score: {score}/100 | IMC: {bmi} ({bmi_cat})")

            if alerts:
                alert_texts = [a.get("message", str(a)) if isinstance(a, dict) else str(a) for a in alerts]
                if language == "en":
                    sections.append(f"Alerts: {'; '.join(alert_texts)}")
                else:
                    sections.append(f"Alertas: {'; '.join(alert_texts)}")

            goals = analysis.get("weekly_goals", [])
            if goals:
                if language == "en":
                    sections.append(f"Goals: {'; '.join(goals[:5])}")
                else:
                    sections.append(f"Objetivos: {'; '.join(goals[:5])}")

            nutrition = (analysis.get("health_plan") or {}).get("nutrition") or {}
            if nutrition:
                cal = nutrition.get("daily_calories", "N/A")
                macro = nutrition.get("macronutrients") or {}
                if language == "en":
                    sections.append(f"Nutrition: {cal} kcal/day | P: {macro.get('protein','?')}g | C: {macro.get('carbs','?')}g | F: {macro.get('fats','?')}g")
                else:
                    sections.append(f"Nutrición: {cal} kcal/día | P: {macro.get('protein','?')}g | C: {macro.get('carbs','?')}g | G: {macro.get('fats','?')}g")

            exercise = (analysis.get("health_plan") or {}).get("exercise") or {}
            if exercise:
                cardio = exercise.get("cardio", "")
                strength = exercise.get("strength", "")
                if language == "en":
                    sections.append(f"Exercise: Cardio: {cardio} | Strength: {strength}")
                else:
                    sections.append(f"Ejercicio: Cardio: {cardio} | Fuerza: {strength}")

        if prediction:
            pred_class = prediction.get("predicted_class") or prediction.get("predictedCategory", "N/A")
            confidence = prediction.get("confidence", "N/A")
            if language == "en":
                sections.append(f"ML Prediction: {pred_class} (Confidence: {confidence}%)")
            else:
                sections.append(f"Predicción ML: {pred_class} (Confianza: {confidence}%)")

        if xai:
            main_reason = xai.get("main_reason", "")
            risk = xai.get("risk_explanation", "")
            recommendations = xai.get("recommendations", [])
            if main_reason or risk:
                if language == "en":
                    parts = []
                    if main_reason:
                        parts.append(f"Main reason: {main_reason}")
                    if risk:
                        parts.append(f"Risk: {risk}")
                    sections.append(" | ".join(parts))
                else:
                    parts = []
                    if main_reason:
                        parts.append(f"Razón principal: {main_reason}")
                    if risk:
                        parts.append(f"Riesgo: {risk}")
                    sections.append(" | ".join(parts))
            if recommendations:
                if language == "en":
                    sections.append(f"Recommendations: {'; '.join(recommendations[:5])}")
                else:
                    sections.append(f"Recomendaciones: {'; '.join(recommendations[:5])}")

        if diary:
            today = diary.get("today") or {}
            streak = diary.get("streak_days", 0)
            parts = []
            if today.get("water_liters"):
                parts.append(f"Agua hoy: {today['water_liters']}L")
            if today.get("calories_consumed"):
                parts.append(f"Calorías hoy: {today['calories_consumed']}kcal")
            if today.get("exercise_minutes"):
                parts.append(f"Ejercicio hoy: {today['exercise_minutes']}min")
            if today.get("sleep_hours"):
                parts.append(f"Sueño hoy: {today['sleep_hours']}h")
            if today.get("mood"):
                mood_labels = {1: 'Muy mal', 2: 'Mal', 3: 'Regular', 4: 'Bien', 5: 'Excelente'}
                parts.append(f"Estado de ánimo: {mood_labels.get(today['mood'], 'N/A')}")
            if today.get("weight_kg"):
                parts.append(f"Peso registrado: {today['weight_kg']}kg")
            if parts:
                if language == "en":
                    sections.append(f"Today's diary: {' | '.join(parts)} | Streak: {streak} days")
                else:
                    sections.append(f"Diario de hoy: {' | '.join(parts)} | Racha: {streak} días")

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
        history: Optional[List[Dict[str, str]]] = None,
        diary: Optional[Dict] = None,
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
        user_context = self._build_user_context(message, analysis, prediction, xai, language, diary)

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history[-15:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                content = msg.get("content", "")
                if content.strip():
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_context})

        try:
            chat_completion = self._client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=512,
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
