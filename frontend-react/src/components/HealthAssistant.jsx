import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

function HealthAssistant({ analysis, latestPrediction, xaiData }) {
  const { t, i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setVoiceSupported(true);
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'es-ES';
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
        handleSend(transcript);
      };
      recognitionRef.current.onerror = () => setIsListening(false);
      recognitionRef.current.onend = () => setIsListening(false);
    }
    synthRef.current = window.speechSynthesis;
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const speak = (text) => {
    if (synthRef.current) {
      synthRef.current.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = i18n.language === 'en' ? 'en-US' : 'es-ES';
      utterance.onstart = () => setSpeaking(true);
      utterance.onend = () => setSpeaking(false);
      synthRef.current.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    synthRef.current?.cancel();
    setSpeaking(false);
  };

  const generateLocalResponse = (query) => {
    const q = query.toLowerCase();
    const lang = i18n.language || 'es';

    if (!analysis) {
      return {
        matched: true,
        text: lang === 'es'
          ? 'Aún no tienes un análisis de salud. Ve al Dashboard y haz clic en "Analizar Salud" primero.'
          : 'You don\'t have a health analysis yet. Go to Dashboard and click "Analyze Health" first.'
      };
    }

    const score = analysis.health_score || analysis.healthScore || 0;
    const bmi = analysis.bmi || 0;
    const alerts = analysis.alerts || [];

    if (q.includes('score') || q.includes('puntuación') || q.includes('salud') || q.includes('health')) {
      return {
        matched: true,
        text: lang === 'es'
          ? `Tu puntuación de salud es ${score}/100. ${score >= 80 ? '¡Excelente! Estás en muy buena forma.' : score >= 60 ? 'Buena puntuación, pero hay áreas de mejora.' : 'Tu puntuación indica que debes prestar atención a tu salud.'}`
          : `Your health score is ${score}/100. ${score >= 80 ? 'Excellent! You\'re in great shape.' : score >= 60 ? 'Good score, but there\'s room for improvement.' : 'Your score indicates you should pay attention to your health.'}`
      };
    }

    if (q.includes('bmi') || q.includes('imc') || q.includes('peso') || q.includes('weight')) {
      const category = bmi < 18.5 ? 'bajo peso' : bmi < 25 ? 'normal' : bmi < 30 ? 'sobrepeso' : 'obesidad';
      return {
        matched: true,
        text: lang === 'es'
          ? `Tu IMC es ${bmi.toFixed(1)}, lo que se considera ${category}. ${bmi >= 25 ? 'Mantener una dieta balanceada y ejercicio regular te ayudará.' : 'Estás en un rango saludable.'}`
          : `Your BMI is ${bmi.toFixed(1)}, which is considered ${category}. ${bmi >= 25 ? 'A balanced diet and regular exercise will help.' : 'You\'re in a healthy range.'}`
      };
    }

    if (q.includes('alerta') || q.includes('alert') || q.includes('riesgo') || q.includes('risk')) {
      if (alerts.length === 0) {
        return {
          matched: true,
          text: lang === 'es'
            ? 'No tienes alertas de salud activas. ¡Sigue así!'
            : 'You have no active health alerts. Keep it up!'
        };
      }
      return {
        matched: true,
        text: lang === 'es'
          ? `Tienes ${alerts.length} alerta(s) activa(s): ${alerts.slice(0, 3).map(a => a.message || a.text || a).join('; ')}. Te recomiendo consultar con un profesional.`
          : `You have ${alerts.length} active alert(s): ${alerts.slice(0, 3).map(a => a.message || a.text || a).join('; ')}. I recommend consulting a professional.`
      };
    }

    if (q.includes('comida') || q.includes('nutrición') || q.includes('nutrition') || q.includes('calorías') || q.includes('calories')) {
      const nutrition = analysis.health_plan?.nutrition || analysis.nutrition || {};
      const calories = nutrition.daily_calories || nutrition.dailyCalories || 2000;
      return {
        matched: true,
        text: lang === 'es'
          ? `Según tu perfil, necesitas aproximadamente ${calories} kcal/día. Tu plan incluye distribución balanceada de macronutrientes. Revisa la pestaña de Nutrición para detalles.`
          : `Based on your profile, you need approximately ${calories} kcal/day. Your plan includes balanced macronutrient distribution. Check the Nutrition tab for details.`
      };
    }

    if (q.includes('ejercicio') || q.includes('exercise') || q.includes('entreno') || q.includes('workout')) {
      return {
        matched: true,
        text: lang === 'es'
          ? `Tu plan de ejercicio está personalizado según tu nivel de actividad. Incluye combinación de cardio, fuerza y flexibilidad. Revisa la pestaña de Ejercicio para tu horario semanal.`
          : `Your exercise plan is personalized based on your activity level. It includes a combination of cardio, strength, and flexibility. Check the Exercise tab for your weekly schedule.`
      };
    }

    if (q.includes('predicción') || q.includes('prediction') || q.includes('futuro') || q.includes('future')) {
      if (latestPrediction) {
        const predicted = latestPrediction.predicted_category || latestPrediction.predictedCategory || latestPrediction.predicted_class || 'N/A';
        return {
          matched: true,
          text: lang === 'es'
            ? `Tu predicción ML indica categoría "${predicted}". El modelo tiene alta confianza en esta predicción. Revisa la pestaña de Predicciones para ver escenarios futuros.`
            : `Your ML prediction indicates category "${predicted}". The model has high confidence in this prediction. Check the Predictions tab for future scenarios.`
        };
      }
      return {
        matched: true,
        text: lang === 'es'
          ? 'Aún no tienes predicciones. Completa tu perfil y analiza tu salud primero.'
          : 'You don\'t have predictions yet. Complete your profile and analyze your health first.'
      };
    }

    if (q.includes('consejo') || q.includes('tip') || q.includes('ayuda') || q.includes('help') || q.includes('recomend')) {
      const tips = [
        lang === 'es' ? 'Mantén hidratación: bebe al menos 2L de agua diarios.' : 'Stay hydrated: drink at least 2L of water daily.',
        lang === 'es' ? 'Duerme 7-8 horas para óptima recuperación.' : 'Sleep 7-8 hours for optimal recovery.',
        lang === 'es' ? 'Incluye vegetales en cada comida principal.' : 'Include vegetables in every main meal.',
        lang === 'es' ? 'Camina al menos 30 minutos al día.' : 'Walk at least 30 minutes daily.'
      ];
      return {
        matched: true,
        text: tips[Math.floor(Math.random() * tips.length)]
      };
    }

    return { matched: false, text: null };
  };

  const callAI = async (query) => {
    const lang = i18n.language || 'es';
    setChatLoading(true);
    setApiError(null);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          language: lang,
          analysis: analysis || null,
          prediction: latestPrediction || null,
          xai: xaiData || null
        })
      });

      const data = await response.json();

      if (data.success) {
        return { text: data.response, source: data.source || 'groq' };
      }
      return { text: data.response || data.message || 'No response from AI', source: 'error' };
    } catch (err) {
      console.error('Chat API error:', err);
      const lang = i18n.language || 'es';
      return {
        text: lang === 'es'
          ? 'Error de conexión con el servicio de IA. Intenta de nuevo.'
          : 'Connection error with AI service. Please try again.',
        source: 'error'
      };
    } finally {
      setChatLoading(false);
    }
  };

  const handleSend = async (textOverride) => {
    const text = textOverride || input.trim();
    if (!text) return;

    const userMsg = { role: 'user', text, time: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsThinking(true);

    const local = generateLocalResponse(text);

    if (local.matched) {
      setTimeout(() => {
        const botMsg = { role: 'assistant', text: local.text, time: new Date(), source: 'local' };
        setMessages(prev => [...prev, botMsg]);
        setIsThinking(false);
      }, 400 + Math.random() * 400);
      return;
    }

    const aiResult = await callAI(text);
    const botMsg = { role: 'assistant', text: aiResult.text, time: new Date(), source: aiResult.source };
    setMessages(prev => [...prev, botMsg]);
    setIsThinking(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => {
          setIsOpen(true);
          if (messages.length === 0) {
            setMessages([{ role: 'assistant', text: t('chat.greeting'), time: new Date(), source: 'system' }]);
          }
        }}
        className="chat-fab"
        title={t('nav.chat')}
      >
        💬
      </button>
    );
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <span style={{ fontSize: '14px', fontWeight: '700' }}>🩺 {t('chat.title')}</span>
        <div style={{ display: 'flex', gap: '6px' }}>
          {voiceSupported && (
            <button
              onClick={toggleListening}
              className="chat-header-btn"
              title={isListening ? t('voice.stop') : t('voice.mic')}
              style={{ color: isListening ? '#ef4444' : 'inherit' }}
            >
              🎙️
            </button>
          )}
          <button onClick={() => setIsOpen(false)} className="chat-header-btn">✕</button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <div className="chat-bubble">
              {msg.source === 'groq' && (
                <span className="chat-ai-badge">AI</span>
              )}
              {msg.text}
              {msg.role === 'assistant' && voiceSupported && (
                <button
                  onClick={() => speaking ? stopSpeaking() : speak(msg.text)}
                  className="chat-speak-btn"
                  title={speaking ? t('chat.stopSpeaking') : t('chat.speakResponse')}
                >
                  {speaking ? '⏹' : '🔊'}
                </button>
              )}
            </div>
          </div>
        ))}
        {(isThinking || chatLoading) && (
          <div className="chat-msg assistant">
            <div className="chat-bubble thinking">
              <span className="dot-pulse"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.placeholder')}
          className="chat-input"
          disabled={isThinking || chatLoading}
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || isThinking || chatLoading}
          className="chat-send-btn"
        >
          ➤
        </button>
      </div>
    </div>
  );
}

export default HealthAssistant;
