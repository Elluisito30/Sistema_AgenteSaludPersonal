import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

const STORAGE_KEY = 'health_ai_conversations';
const MAX_HISTORY = 15;

function loadConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveConversations(convs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
}

function makeId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function autoRename(messages) {
  const firstUser = messages.find(m => m.role === 'user');
  if (!firstUser) return null;
  const text = firstUser.text.slice(0, 40);
  return text.length < firstUser.text.length ? text + '...' : text;
}

function relativeDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = now - d;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Ahora';
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d`;
  return d.toLocaleDateString();
}

function lastMessagePreview(convo) {
  const msgs = convo.messages.filter(m => m.role === 'user');
  if (msgs.length === 0) return '';
  const last = msgs[msgs.length - 1].text;
  return last.length > 50 ? last.slice(0, 50) + '...' : last;
}

function HealthAssistant({ analysis, latestPrediction, xaiData }) {
  const { t, i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [conversations, setConversations] = useState(loadConversations);
  const [activeId, setActiveId] = useState(null);
  const [input, setInput] = useState('');
  const [interimText, setInterimText] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [micPermission, setMicPermission] = useState('unknown');
  const [autoRead, setAutoRead] = useState(true);
  const [continuousMode, setContinuousMode] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const autoReadRef = useRef(autoRead);
  const continuousModeRef = useRef(continuousMode);
  const inputRef = useRef(null);

  useEffect(() => { autoReadRef.current = autoRead; }, [autoRead]);
  useEffect(() => { continuousModeRef.current = continuousMode; }, [continuousMode]);

  const activeConvo = conversations.find(c => c.id === activeId);
  const messages = activeConvo ? activeConvo.messages : [];

  const updateConvo = useCallback((id, updater) => {
    setConversations(prev => {
      const next = prev.map(c => c.id === id ? updater({ ...c }) : c);
      saveConversations(next);
      return next;
    });
  }, []);

  useEffect(() => {
    saveConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    setVoiceSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = i18n.language === 'en' ? 'en-US' : 'es-ES';
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }
      if (final) {
        setInput(final);
        setInterimText('');
      } else if (interim) {
        setInterimText(interim);
      }
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      setInterimText('');
      if (event.error === 'not-allowed') {
        setMicPermission('denied');
      } else if (event.error === 'no-speech') {
        setMicPermission('ok');
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimText('');
    };

    recognitionRef.current = recognition;
    synthRef.current = window.speechSynthesis;
  }, [i18n.language]);

  useEffect(() => {
    if (i18n.language && recognitionRef.current) {
      recognitionRef.current.lang = i18n.language === 'en' ? 'en-US' : 'es-ES';
    }
  }, [i18n.language]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking, chatLoading, interimText]);

  const speak = useCallback((text) => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = i18n.language === 'en' ? 'en-US' : 'es-ES';
    utterance.rate = 1.0;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => {
      setSpeaking(false);
      if (continuousModeRef.current) {
        setTimeout(() => startListening(), 400);
      }
    };
    synthRef.current.speak(utterance);
  }, [i18n.language]);

  const stopSpeaking = () => {
    synthRef.current?.cancel();
    setSpeaking(false);
  };

  const startListening = () => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.lang = i18n.language === 'en' ? 'en-US' : 'es-ES';
      recognitionRef.current.start();
      setIsListening(true);
    } catch (e) {
      if (e.name === 'NotAllowedError') {
        setMicPermission('denied');
      }
    }
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      setInterimText('');
    } else {
      navigator.mediaDevices?.getUserMedia({ audio: true })
        .then((stream) => {
          stream.getTracks().forEach(t => t.stop());
          setMicPermission('ok');
          startListening();
        })
        .catch(() => {
          setMicPermission('denied');
        });
    }
  };

  const createNewChat = () => {
    const id = makeId();
    const newConvo = {
      id,
      title: t('chat.untitledChat'),
      messages: [{ role: 'assistant', text: t('chat.greeting'), time: new Date().toISOString(), source: 'system' }],
      createdAt: new Date().toISOString(),
    };
    setConversations(prev => {
      const next = [newConvo, ...prev];
      saveConversations(next);
      return next;
    });
    setActiveId(id);
  };

  const switchChat = (id) => {
    setActiveId(id);
  };

  const deleteChat = (id) => {
    setConversations(prev => {
      const next = prev.filter(c => c.id !== id);
      saveConversations(next);
      return next;
    });
    if (activeId === id) {
      setActiveId(conversations.length > 1 ? conversations.find(c => c.id !== id)?.id : null);
    }
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
    const nutrition = analysis.health_plan?.nutrition || analysis.nutrition || {};
    const calories = nutrition.daily_calories || nutrition.dailyCalories || 2000;

    if (q.includes('score') || q.includes('puntuación') || q.includes('salud') || q.includes('health')) {
      return {
        matched: true,
        text: lang === 'es'
          ? `Tu puntuación de salud es ${score}/100. ${score >= 80 ? '¡Excelente! Estás en muy buena forma.' : score >= 60 ? 'Buena puntuación, pero hay áreas de mejora.' : 'Tu puntuación indica que debes prestar atención a tu salud.'}`
          : `Your health score is ${score}/100. ${score >= 80 ? 'Excellent! You\'re in great shape.' : score >= 60 ? 'Good score, but there\'s room for improvement.' : 'Your score indicates you should pay attention to your health.'}`
      };
    }

    if (q.includes('bmi') || q.includes('imc') || q.includes('peso') || q.includes('weight')) {
      const cat = bmi < 18.5 ? (lang === 'es' ? 'bajo peso' : 'underweight') : bmi < 25 ? (lang === 'es' ? 'normal' : 'normal') : bmi < 30 ? (lang === 'es' ? 'sobrepeso' : 'overweight') : (lang === 'es' ? 'obesidad' : 'obese');
      return {
        matched: true,
        text: lang === 'es'
          ? `Tu IMC es ${bmi.toFixed(1)}, lo que se considera ${cat}. ${bmi >= 25 ? 'Una dieta balanceada y ejercicio regular te ayudarán a mejorar.' : 'Estás en un rango saludable.'}`
          : `Your BMI is ${bmi.toFixed(1)}, which is considered ${cat}. ${bmi >= 25 ? 'A balanced diet and regular exercise will help.' : 'You\'re in a healthy range.'}`
      };
    }

    if (q.includes('alerta') || q.includes('alert') || q.includes('riesgo') || q.includes('risk')) {
      if (alerts.length === 0) {
        return { matched: true, text: lang === 'es' ? 'No tienes alertas de salud activas. ¡Sigue así!' : 'You have no active health alerts. Keep it up!' };
      }
      return {
        matched: true,
        text: lang === 'es'
          ? `Tienes ${alerts.length} alerta(s): ${alerts.slice(0, 2).map(a => a.message || a.text || a).join('; ')}. Te recomiendo consultar con un profesional.`
          : `You have ${alerts.length} alert(s): ${alerts.slice(0, 2).map(a => a.message || a.text || a).join('; ')}. I recommend consulting a professional.`
      };
    }

    if (q.includes('comida') || q.includes('nutrición') || q.includes('nutrition') || q.includes('calorías') || q.includes('calories') || q.includes('comer') || q.includes('alimento')) {
      return {
        matched: true,
        text: lang === 'es'
          ? `Necesitas aproximadamente ${calories} kcal/día. Algunas ideas: proteína magra (pollo, pescado, huevos), vegetales variados, carbohidratos complexos (arroz integral, avena) y grasas saludables (aguacate, nueces). ¿Quieres que te sugiera algo más específico?`
          : `You need approximately ${calories} kcal/day. Some ideas: lean protein (chicken, fish, eggs), varied vegetables, complex carbs (brown rice, oats) and healthy fats (avocado, nuts). Want something more specific?`
      };
    }

    if (q.includes('ejercicio') || q.includes('exercise') || q.includes('entreno') || q.includes('workout') || q.includes('actividad')) {
      return {
        matched: true,
        text: lang === 'es'
          ? 'Basándome en tu nivel de actividad, te recomiendo: 30 min de caminata diaria, 2-3 sesiones de fuerza por semana, y estiramientos para flexibilidad. Lo importante es ser constante. ¿Cuál es tu nivel actual de actividad?'
          : 'Based on your activity level, I recommend: 30 min of daily walking, 2-3 strength sessions per week, and stretching for flexibility. Consistency is key. What\'s your current activity level?'
      };
    }

    if (q.includes('predicción') || q.includes('prediction') || q.includes('futuro') || q.includes('future')) {
      if (latestPrediction) {
        const predicted = latestPrediction.predicted_category || latestPrediction.predictedCategory || latestPrediction.predicted_class || 'N/A';
        return {
          matched: true,
          text: lang === 'es'
            ? `Tu predicción indica categoría "${predicted}". El modelo tiene buena confianza en esto. ¿Qué te gustaría hacer para mejorar tu proyección?`
            : `Your prediction indicates category "${predicted}". The model has good confidence. What would you like to do to improve your projection?`
        };
      }
      return { matched: true, text: lang === 'es' ? 'Aún no tienes predicciones. Completa tu perfil y analiza tu salud primero.' : 'You don\'t have predictions yet. Complete your profile and analyze your health first.' };
    }

    if (q.includes('mejorar') || q.includes('improve') || q.includes('qué puedo hacer') || q.includes('qué hago')) {
      const s = [];
      if (bmi >= 25) s.push(lang === 'es' ? 'trabajar en tu peso' : 'work on your weight');
      if (score < 70) s.push(lang === 'es' ? 'mejorar tu puntuación general' : 'improve your overall score');
      if (alerts.length > 0) s.push(lang === 'es' ? 'atender tus alertas activas' : 'address your active alerts');
      s.push(lang === 'es' ? 'aumentar tu actividad diaria' : 'increase your daily activity');
      return {
        matched: true,
        text: lang === 'es'
          ? `Podrías enfocarte en: ${s.slice(0, 3).join(', ')}. Lo más importante es la consistencia. ¿Quieres que profundicemos en alguno?`
          : `You could focus on: ${s.slice(0, 3).join(', ')}. The most important thing is consistency. Want to dive deeper into any?`
      };
    }

    if (q.includes('dormir') || q.includes('sleep') || q.includes('sueño')) {
      return {
        matched: true,
        text: lang === 'es'
          ? 'Para mejorar tu sueño: intenta acostarte a la misma hora, evita pantallas 1 hora antes, mantén la habitación fresca y oscura, y evita cafeína después de las 2pm. Dormir 7-8 horas es ideal. ¿Tienes problemas para dormir?'
          : 'To improve your sleep: try going to bed at the same time, avoid screens 1 hour before, keep the room cool and dark, and avoid caffeine after 2pm. 7-8 hours is ideal. Having trouble sleeping?'
      };
    }

    if (q.includes('consejo') || q.includes('tip') || q.includes('ayuda') || q.includes('help') || q.includes('recomend')) {
      return {
        matched: true,
        text: lang === 'es'
          ? 'Un hábito que marca diferencia: camina 30 minutos al día, bebe 2L de agua, duerme bien y incluye vegetales en cada comida. Son simples pero efectivos. ¿Qué área te gustaría mejorar primero?'
          : 'One habit that makes a difference: walk 30 minutes daily, drink 2L of water, sleep well, and include vegetables in every meal. Simple but effective. Which area would you like to improve first?'
      };
    }

    return { matched: false, text: null };
  };

  const callAI = async (query) => {
    const lang = i18n.language || 'es';
    setChatLoading(true);

    const historyForBackend = messages.map(m => ({
      role: m.role === 'assistant' ? 'assistant' : 'user',
      content: m.text
    }));

    let diaryData = null;
    try {
      const diaryRes = await fetch('/api/diary/summary');
      if (diaryRes.ok) diaryData = await diaryRes.json();
    } catch (e) { /* ignore */ }

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          language: lang,
          analysis: analysis || null,
          prediction: latestPrediction || null,
          xai: xaiData || null,
          history: historyForBackend.slice(-MAX_HISTORY),
          diary: diaryData || null,
        })
      });

      const data = await response.json();
      if (data.success) {
        return { text: data.response, source: data.source || 'groq' };
      }
      return { text: data.response || data.message || 'No response from AI', source: 'error' };
    } catch (err) {
      console.error('Chat API error:', err);
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
    if (!text || !activeId) return;

    const userMsg = { role: 'user', text, time: new Date().toISOString() };
    updateConvo(activeId, c => ({ ...c, messages: [...c.messages, userMsg] }));
    setInput('');
    setInterimText('');
    setIsThinking(true);

    const local = generateLocalResponse(text);

    let botMsg;
    if (local.matched) {
      botMsg = { role: 'assistant', text: local.text, time: new Date().toISOString(), source: 'local' };
    } else {
      const aiResult = await callAI(text);
      botMsg = { role: 'assistant', text: aiResult.text, time: new Date().toISOString(), source: aiResult.source };
    }

    updateConvo(activeId, c => {
      const newMsgs = [...c.messages, botMsg];
      const titleChanged = c.title === t('chat.untitledChat') || !c.title;
      return {
        ...c,
        messages: newMsgs,
        ...(titleChanged ? { title: autoRename(newMsgs) || c.title } : {})
      };
    });
    setIsThinking(false);

    if (autoReadRef.current && botMsg.role === 'assistant') {
      setTimeout(() => speak(botMsg.text), 200);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (input && isThinking === false && chatLoading === false) {
      recognitionRef.current?.stop();
      setIsListening(false);
      setInterimText('');
    }
  }, [input]);

  if (!isOpen) {
    return (
      <button
        onClick={() => {
          setIsOpen(true);
          if (!activeId) createNewChat();
        }}
        className="chat-fab"
        title={t('nav.chat')}
      >
        💬
      </button>
    );
  }

  const showInterim = interimText && isThinking === false && chatLoading === false;

  return (
    <div className="chat-window chat-with-sidebar">
      {showSidebar && (
        <div className="chat-sidebar">
          <div className="chat-sidebar-header">
            <span className="chat-sidebar-title">{t('chat.chatHistory')}</span>
            <button onClick={() => setShowSidebar(false)} className="chat-sidebar-close">✕</button>
          </div>
          <button onClick={createNewChat} className="chat-sidebar-new">
            + {t('chat.newChat')}
          </button>
          <div className="chat-sidebar-list">
            {conversations.map(c => (
              <div
                key={c.id}
                className={`chat-sidebar-item ${c.id === activeId ? 'active' : ''}`}
                onClick={() => switchChat(c.id)}
              >
                <div className="chat-sidebar-item-content">
                  <div className="chat-sidebar-item-title">{c.title}</div>
                  <div className="chat-sidebar-item-preview">{lastMessagePreview(c)}</div>
                  <div className="chat-sidebar-item-meta">
                    <span className="chat-sidebar-item-date">{relativeDate(c.createdAt)}</span>
                    <span className="chat-sidebar-item-count">{c.messages.filter(m => m.role === 'user').length}</span>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }}
                  className="chat-sidebar-item-delete"
                  title={t('chat.deleteChat')}
                >
                  🗑
                </button>
              </div>
            ))}
            {conversations.length === 0 && (
              <div className="chat-sidebar-empty">{t('chat.noMessages')}</div>
            )}
          </div>
        </div>
      )}

      <div className="chat-main">
        <div className="chat-header">
          <div className="chat-header-left">
            <button onClick={() => setShowSidebar(!showSidebar)} className="chat-header-btn" title={t('chat.chatHistory')}>
              ☰
            </button>
            <span className="chat-header-title">🩺 {t('chat.title')}</span>
          </div>
          <div className="chat-header-right">
            {voiceSupported && (
              <>
                <button
                  onClick={() => setAutoRead(!autoRead)}
                  className={`chat-header-btn ${autoRead ? 'active-toggle' : ''}`}
                  title={`${t('chat.autoRead')}: ${autoRead ? t('chat.autoReadOn') : t('chat.autoReadOff')}`}
                >
                  🔊
                </button>
                <button
                  onClick={() => setContinuousMode(!continuousMode)}
                  className={`chat-header-btn ${continuousMode ? 'active-toggle' : ''}`}
                  title={`${t('chat.continuousMode')}: ${continuousMode ? t('chat.continuousModeOn') : ''}`}
                >
                  🔄
                </button>
                <button
                  onClick={toggleListening}
                  className={`chat-header-btn mic-btn ${isListening ? 'recording' : ''}`}
                  title={isListening ? t('voice.stop') : t('voice.mic')}
                >
                  {isListening && <span className="mic-pulse" />}
                  🎙️
                </button>
              </>
            )}
            <button onClick={() => { setIsOpen(false); setShowSidebar(false); }} className="chat-header-btn">✕</button>
          </div>
        </div>

        {micPermission === 'denied' && (
          <div className="chat-mic-error">
            ⚠️ {t('chat.micPermissionDenied')}
          </div>
        )}

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty-state">
              <span style={{ fontSize: 32 }}>🩺</span>
              <p>{t('chat.greeting')}</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className="chat-bubble">
                {msg.source === 'groq' && (
                  <span className="chat-ai-badge">AI</span>
                )}
                {msg.text}
                {msg.role === 'assistant' && msg.source !== 'system' && voiceSupported && (
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
          {showInterim && (
            <div className="chat-msg user">
              <div className="chat-bubble interim">{interimText}</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {isListening && (
          <div className="chat-recording-bar">
            <div className="voice-bars">
              <span /><span /><span /><span /><span />
            </div>
            <span className="recording-text">{t('voice.recording')}</span>
          </div>
        )}

        <div className="chat-input-area">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isListening ? t('chat.transcriptPlaceholder') : t('chat.placeholder')}
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
    </div>
  );
}

export default HealthAssistant;
