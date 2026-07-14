import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import Plot from 'react-plotly.js';
import './Dashboard.css';

function Dashboard() {
  const { token, user, logout } = useAuth();
  const { apiRequest } = useApi();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [profile, setProfile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [latestPrediction, setLatestPrediction] = useState(null);
  const [predictionsHistory, setPredictionsHistory] = useState(null);
  const [timelineData, setTimelineData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [sleepHours, setSleepHours] = useState(7);
  const [reportLanguage, setReportLanguage] = useState('es');

  // Load profile on mount
  useEffect(() => {
    loadProfile();
    if (activeTab === 'predictions' || activeTab === 'dashboard') {
      loadPredictions();
    }
  }, [activeTab]);

  const loadProfile = async () => {
    const result = await apiRequest('/api/profile', 'GET', null, token);
    if (result.success) {
      setProfile(result.data);
      setSleepHours(result.data.sleep_hours || 7);
    }
  };

  const loadPredictions = async () => {
    setLoading(true);
    try {
      const latest = await apiRequest('/api/predictions/latest', 'GET', null, token);
      if (latest.success) {
        setLatestPrediction(latest.data);
      }
      const history = await apiRequest('/api/predictions/history?limit=5', 'GET', null, token);
      if (history.success) {
        setPredictionsHistory(history.data);
      }
      const timeline = await apiRequest('/api/predictions/timeline', 'GET', null, token);
      if (timeline.success) {
        setTimelineData(timeline.data);
      }
      const stats = await apiRequest('/api/predictions/stats', 'GET', null, token);
      if (stats.success) {
        setStatsData(stats.data);
      }
    } catch (e) {
      console.error('Error loading predictions:', e);
    }
    setLoading(false);
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setLoading(true);

    const healthGoalsSelect = e.target.healthGoals;
    const selectedGoals = Array.from(healthGoalsSelect.selectedOptions).map(opt => opt.value);

    const data = {
      age: parseInt(e.target.age.value),
      gender: e.target.gender.value,
      height_cm: parseFloat(e.target.height.value),
      weight_kg: parseFloat(e.target.weight.value),
      activity_level: e.target.activityLevel.value,
      sleep_hours: sleepHours,
      smokes: e.target.smokes.checked,
      has_chronic_conditions: e.target.hasChronic.checked,
      chronic_conditions_detail: e.target.chronicDetail ? e.target.chronicDetail.value : '',
      genetics_risk: e.target.geneticsRisk ? e.target.geneticsRisk.value : 'low',
      health_goals: selectedGoals,
      family_history: e.target.familyHistory ? e.target.familyHistory.checked : false,
      favc: e.target.favc ? e.target.favc.value : 'Sometimes',
      fcvc: e.target.fcvc ? parseFloat(e.target.fcvc.value) : 2.0,
      ch2o: e.target.ch2o ? parseFloat(e.target.ch2o.value) : 2.0,
    };

    const result = await apiRequest('/api/profile', 'POST', data, token);
    if (result.success) {
      setProfile(data);
      setMessage({ type: 'success', text: '✅ Perfil actualizado correctamente' });
      await analyzeHealth();
    } else {
      setMessage({ type: 'error', text: result.error });
    }
    setLoading(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const analyzeHealth = async () => {
    setLoading(true);
    setMessage({ type: 'info', text: 'Analizando tu salud con IA...' });

    const result = await apiRequest('/api/analyze', 'POST', null, token);

    if (result.success) {
      setAnalysis(result.data);
      setMessage({ type: 'success', text: '✅ Análisis completado con éxito' });
      await loadPredictions();
    } else {
      setMessage({ type: 'error', text: result.error });
    }
    setLoading(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const getScoreClass = (score) => {
    if (score >= 80) return 'health-score-excellent';
    if (score >= 60) return 'health-score-good';
    return 'health-score-warning';
  };

  const getScoreText = (score) => {
    if (score >= 80) return 'Excelente';
    if (score >= 60) return 'Bueno';
    return 'Mejorable';
  };

  const getScoreColorVar = (score) => {
    if (score < 40) return 'var(--danger)';
    if (score <= 60) return 'var(--accent)';
    if (score <= 80) return 'var(--accent)';
    return 'var(--secondary)';
  };

  const getScoreBorderClass = (score) => {
    if (score < 40) return 'score-danger';
    if (score <= 60) return 'score-accent';
    if (score <= 80) return 'score-warning';
    return 'score-good';
  };

  const downloadReport = async (endpoint, filename) => {
    try {
      const response = await fetch(`${endpoint}?language=${reportLanguage}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        console.error('Error downloading report:', response.statusText);
      }
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const getChartLayout = (title, isBar = false, isPie = false) => {
    const baseFont = { family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif', color: '#475569' };
    const titleFont = { ...baseFont, size: 15, color: '#1e293b' };

    if (isPie) {
      return {
        title: { text: title, font: titleFont, x: 0.02, xanchor: 'left' },
        paper_bgcolor: 'rgba(255,255,255,0)',
        plot_bgcolor: 'rgba(255,255,255,0)',
        height: 360,
        margin: { t: 44, b: 24, l: 16, r: 16 },
        font: baseFont,
        showlegend: true,
        legend: {
          x: 0.5,
          y: -0.15,
          xanchor: 'center',
          orientation: 'h',
          font: { size: 12, color: '#475569' }
        },
        hoverlabel: {
          bgcolor: '#1e293b',
          bordercolor: '#1e293b',
          font: { family: baseFont.family, size: 13, color: '#ffffff' }
        }
      };
    }
    return {
      title: { text: title, font: titleFont, x: 0.02, xanchor: 'left' },
      paper_bgcolor: 'rgba(255,255,255,0)',
      plot_bgcolor: 'rgba(255,255,255,0)',
      height: 360,
      margin: { t: 44, b: 56, l: 52, r: 20 },
      font: baseFont,
      hoverlabel: {
        bgcolor: '#1e293b',
        bordercolor: '#1e293b',
        font: { family: baseFont.family, size: 13, color: '#ffffff' }
      },
      xaxis: {
        tickfont: { size: 12, color: '#64748b' },
        gridcolor: '#f1f5f9',
        zerolinecolor: '#e2e8f0'
      },
      yaxis: {
        tickfont: { size: 12, color: '#64748b' },
        gridcolor: '#f1f5f9',
        zerolinecolor: '#e2e8f0'
      },
      bargap: 0.35,
      legend: {
        font: { size: 12, color: '#475569' }
      }
    };
  };

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="app-logo">
            🏥 Health AI
          </div>
          <div className="user-card">
            <div className="user-avatar">{user?.full_name?.[0]?.toUpperCase() || 'U'}</div>
            <div className="user-info">
              <div className="user-name">{user?.full_name || 'Usuario'}</div>
              <div className="user-email">{user?.email || ''}</div>
            </div>
          </div>
        </div>

        <nav className="nav-menu">
          <button
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={`nav-item ${activeTab === 'nutrition' ? 'active' : ''}`}
            onClick={() => setActiveTab('nutrition')}
          >
            🥗 Nutrición
          </button>
          <button
            className={`nav-item ${activeTab === 'exercise' ? 'active' : ''}`}
            onClick={() => setActiveTab('exercise')}
          >
            💪 Ejercicio
          </button>
          <button
            className={`nav-item ${activeTab === 'predictions' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('predictions');
              loadPredictions();
            }}
          >
            📈 Predicciones
          </button>
          <button
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('reports');
              loadPredictions();
            }}
          >
            📑 Reportes
          </button>
        </nav>

        <button className="btn-logout" onClick={logout}>
          🚪 Cerrar Sesión
        </button>
      </aside>

      <main className="main-content">
        <h1 className="page-title">Tu Salud Personalizada</h1>
        <p className="page-subtitle">Monitorea, analiza y mejora tu bienestar con inteligencia artificial</p>

        {message && (
          <div className={`message ${message.type}`}>
            <span className="message-icon">
              {message.type === 'success' ? '✓' : message.type === 'error' ? '✕' : 'ℹ'}
            </span>
            {message.text}
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="tab-content">
            <div className="analysis-grid">
              <div>
                <div className="profile-section">
                  <h3>📝 Mi Perfil</h3>
                  <form key={profile ? 'loaded' : 'new'} onSubmit={saveProfile} className="profile-form" id="profileForm">
                    <div className="form-section-title">Datos Personales</div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Edad</label>
                        <input
                          type="number"
                          name="age"
                          defaultValue={profile?.age || ''}
                          min="18"
                          max="100"
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Peso (kg)</label>
                        <input
                          type="number"
                          name="weight"
                          step="0.1"
                          defaultValue={profile?.weight_kg || ''}
                          min="30"
                          max="200"
                          required
                        />
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Altura (cm)</label>
                        <input
                          type="number"
                          name="height"
                          step="0.1"
                          defaultValue={profile?.height_cm || ''}
                          min="100"
                          max="220"
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Género</label>
                        <select name="gender" defaultValue={profile?.gender || ''} required>
                          <option value="" disabled>Elegir...</option>
                          <option value="male">Hombre</option>
                          <option value="female">Mujer</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-section-title">Estilo de Vida</div>
                    <div className="form-group">
                      <label>Nivel de Actividad</label>
                      <select name="activityLevel" defaultValue={profile?.activity_level || ''} required>
                        <option value="" disabled>Elegir...</option>
                        <option value="sedentary">Sedentario</option>
                        <option value="light">Ligero</option>
                        <option value="moderate">Moderado</option>
                        <option value="active">Activo</option>
                        <option value="very_active">Muy activo</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Horas de sueño: {sleepHours}</label>
                      <input
                        type="range"
                        name="sleepHours"
                        min="4"
                        max="12"
                        value={sleepHours}
                        onChange={(e) => setSleepHours(parseInt(e.target.value))}
                      />
                    </div>

                    <div className="form-group">
                      <label>Riesgo Genético Familiar</label>
                      <select name="geneticsRisk" defaultValue={profile?.genetics_risk || 'low'}>
                        <option value="low">Bajo (Sin antecedentes graves)</option>
                        <option value="medium">Medio (Algunos antecedentes leves)</option>
                        <option value="high">Alto (Antecedentes directos graves)</option>
                      </select>
                    </div>

                    <div className="form-section-title">Salud</div>
                    <div className="form-check">
                      <input type="checkbox" name="smokes" defaultChecked={profile?.smokes} id="smokes" />
                      <label htmlFor="smokes">Fumador</label>
                    </div>

                    <div className="form-check">
                      <input type="checkbox" name="hasChronic" defaultChecked={profile?.has_chronic_conditions} id="hasChronic" onChange={(e) => {
                        const detailInput = document.getElementById('chronicDetailContainer');
                        if (detailInput) detailInput.style.display = e.target.checked ? 'block' : 'none';
                      }} />
                      <label htmlFor="hasChronic">Condiciones crónicas</label>
                    </div>

                    <div className="form-group" id="chronicDetailContainer" style={{ display: profile?.has_chronic_conditions ? 'block' : 'none', marginTop: '10px' }}>
                      <label>Detalle de condiciones</label>
                      <input type="text" name="chronicDetail" defaultValue={profile?.chronic_conditions_detail || ''} placeholder="Ej. Diabetes, Hipertensión..." />
                    </div>

                    <div className="form-check">
                      <input type="checkbox" name="familyHistory" defaultChecked={profile?.family_history} id="familyHistory" />
                      <label htmlFor="familyHistory">Antecedentes familiares de obesidad</label>
                    </div>

                    <div className="form-section-title">Nutrición</div>
                    <div className="form-group">
                      <label>¿Consume frecuentemente comida chatarra? (FAVC)</label>
                      <select name="favc" defaultValue={profile?.favc || 'Sometimes'}>
                        <option value="Always">Siempre</option>
                        <option value="Frequently">Frecuentemente</option>
                        <option value="Sometimes">A veces</option>
                        <option value="No">No</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>¿Cuántas veces come vegetales por comida? (FCVC)</label>
                      <select name="fcvc" defaultValue={profile?.fcvc || 2.0}>
                        <option value="1">1 — Casi nunca</option>
                        <option value="2">2 — A veces</option>
                        <option value="3">3 — Siempre</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Litros de agua diarios (CH2O)</label>
                      <select name="ch2o" defaultValue={profile?.ch2o || 2.0}>
                        <option value="1">Menos de 1L</option>
                        <option value="2">1–2 Litros</option>
                        <option value="3">Más de 2 Litros</option>
                      </select>
                    </div>

                    <div className="form-section-title">Objetivos</div>
                    <div className="form-group">
                      <label>Objetivos de Salud</label>
                      <select name="healthGoals" multiple defaultValue={profile?.health_goals || []} size="6" required>
                        <option value="weight_loss">📉 Pérdida de peso</option>
                        <option value="muscle_gain">💪 Ganancia muscular</option>
                        <option value="better_sleep">😴 Mejor sueño</option>
                        <option value="stress_reduction">🧘 Reducción estrés</option>
                        <option value="energy_boost">⚡ Más energía</option>
                        <option value="general_wellness">🌟 Bienestar general</option>
                      </select>
                    </div>
                  </form>
                </div>

                <div className="analyze-button-area">
                  <button
                    type="submit"
                    form="profileForm"
                    className={`btn-primary btn-large ${loading ? 'loading' : ''}`}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="btn-loading-spinner"></span>
                        Analizando...
                      </>
                    ) : (
                      '🤖 Analizar mi Salud'
                    )}
                  </button>
                </div>
              </div>

              <div className="analysis-results">
                {analysis ? (
                  <div>
                    <div className="analysis-top-cards">
                      <div className={`analysis-card score ${getScoreBorderClass(analysis.health_score)}`}>
                        <div className="analysis-card-icon" title="Tu puntuación general de salud basada en todos los factores analizados">❤️</div>
                        <div className="analysis-card-label">Health Score</div>
                        <div className="analysis-card-value tooltip-trigger" title="Puntuación de 0 a 100 que refleja tu estado general de salud. Más alto = mejor." style={{ color: getScoreColorVar(analysis.health_score) }}>
                          {analysis.health_score}<span className="score-value-suffix">/100</span>
                        </div>
                        <div className="analysis-card-desc">Puntuación general de salud</div>
                        <span className={`analysis-card-badge ${analysis.health_score < 60 ? 'warning' : analysis.health_score >= 80 ? '' : 'info'}`}>
                          {getScoreText(analysis.health_score)}
                        </span>
                      </div>

                      <div className="analysis-card bmi">
                        <div className="analysis-card-icon" title="Índice de Masa Corporal — relación entre tu peso y tu estatura">⚖️</div>
                        <div className="analysis-card-label">IMC</div>
                        <div className="analysis-card-value tooltip-trigger" title={`IMC: ${analysis.bmi} — Categoría: ${analysis.bmi_category.replace('_', ' ')}. Valores normales: 18.5 – 24.9`}>{analysis.bmi}</div>
                        <div className="analysis-card-desc">Índice de masa corporal</div>
                        <span className={`analysis-card-badge ${analysis.bmi_category === 'normal' ? '' : analysis.bmi_category === 'obese' ? 'danger' : 'warning'}`}>
                          {analysis.bmi_category.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="analysis-card calories">
                        <div className="analysis-card-icon" title="Total de Energía Diaria Expendida — calorías que tu cuerpo necesita al día">🔥</div>
                        <div className="analysis-card-label">Calorías Diarias</div>
                        <div className="analysis-card-value tooltip-trigger" title={`TDEE: ${analysis.tdee?.toFixed(0)} kcal/día. Calculado según tu nivel de actividad, peso, altura y objetivo.`}>{analysis.tdee?.toFixed(0)}</div>
                        <div className="analysis-card-desc">kcal/día según tu objetivo</div>
                        <span className="analysis-card-badge info">TDEE</span>
                      </div>
                    </div>

                    <div className="analysis-panels">
                      <div className="analysis-panel alerts">
                        <h3>🚨 Alertas</h3>
                        <p className="analysis-panel-subtitle">Atención médica y recomendaciones urgentes</p>
                        <div className="analysis-panel-content">
                          {analysis.alerts && analysis.alerts.length > 0 ? (
                            analysis.alerts.map((alert, i) => (
                              <p key={i}>
                                {alert.priority === 'high' || alert.message.includes('Clínica') ? '🚨' : '⚠️'} {alert.message}
                              </p>
                            ))
                          ) : (
                            <p>✅ No tienes alertas médicas críticas en este momento.</p>
                          )}
                        </div>
                      </div>

                      <div className="analysis-panel goals">
                        <h3>🎯 Objetivos</h3>
                        <p className="analysis-panel-subtitle">Metas semanales para mejorar tu bienestar</p>
                        <div className="analysis-panel-content">
                          {analysis.weekly_goals && analysis.weekly_goals.length > 0 ? (
                            analysis.weekly_goals.map((goal, i) => (
                              <p key={i}>🎯 {goal}</p>
                            ))
                          ) : (
                            <p>No hay objetivos asignados.</p>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="analysis-charts">
                      <div className="analysis-chart-card">
                        <h3>Comparativa de Health Score</h3>
                        <p className="analysis-chart-card-subtitle">Tu puntuación vs promedio poblacional</p>
                        <Plot
                          data={[
                            {
                              type: 'bar',
                              name: 'Tu Puntuación',
                              x: ['Health Score'],
                              y: [analysis.health_score],
                              marker: {
                                color: getScoreColorVar(analysis.health_score)
                              }
                            },
                            {
                              type: 'bar',
                              name: 'Promedio Población',
                              x: ['Health Score'],
                              y: [(profile?.age || 30) < 40 ? 75 : 65],
                              marker: { color: 'var(--info)' }
                            }
                          ]}
                          layout={getChartLayout('Comparativa de Health Score', true)}
                          style={{ width: '100%' }}
                        />
                      </div>

                      <div className="analysis-chart-card">
                        <h3>Distribución de Macronutrientes</h3>
                        <p className="analysis-chart-card-subtitle">Proporción diaria de proteínas, carbohidratos y grasas</p>
                        {analysis.health_plan?.nutrition?.macronutrients ? (
                          <Plot
                            data={[
                              {
                                type: 'pie',
                                labels: ['Proteínas', 'Carbohidratos', 'Grasas'],
                                values: [
                                  analysis.health_plan.nutrition.macronutrients.protein,
                                  analysis.health_plan.nutrition.macronutrients.carbs,
                                  analysis.health_plan.nutrition.macronutrients.fats
                                ],
                                hole: 0.5,
                                marker: {
                                  colors: ['#10b981', '#3b82f6', '#f59e0b']
                                },
                                textinfo: 'label+percent',
                                textfont: {
                                  color: '#1e293b'
                                }
                              }
                            ]}
                            layout={getChartLayout('Distribución de Macronutrientes', false, true)}
                            style={{ width: '100%' }}
                          />
                        ) : (
                          <p className="analysis-no-data-msg">
                            No hay datos de macronutrientes disponibles.
                          </p>
                        )}
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <h3>Analiza tu salud para empezar</h3>
                    <p>Completa tu perfil y haz clic en "Analizar mi Salud" para obtener recomendaciones personalizadas</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'nutrition' && (
          <div className="tab-content">
            {analysis?.health_plan?.nutrition ? (
              <div>
                <div className="metrics-grid metrics-grid-spaced">
                  <div className="metric-card" title="Calorías recomendadas diarias para tu objetivo actual">
                    <div className="metric-icon">🔥</div>
                    <div className="metric-label">Calorías Diarias</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.daily_calories}</div>
                    <div className="metric-desc">kcal</div>
                  </div>
                  <div className="metric-card" title={`Proteínas: ${analysis.health_plan.nutrition.macronutrients.protein}g — esenciales para músculo y recuperación`}>
                    <div className="metric-icon">🥩</div>
                    <div className="metric-label">Proteínas</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.protein}g</div>
                  </div>
                  <div className="metric-card" title={`Carbohidratos: ${analysis.health_plan.nutrition.macronutrients.carbs}g — principal fuente de energía`}>
                    <div className="metric-icon">🍚</div>
                    <div className="metric-label">Carbohidratos</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.carbs}g</div>
                  </div>
                  <div className="metric-card" title={`Grasas: ${analysis.health_plan.nutrition.macronutrients.fats}g — necesarias para hormonas y absorción de vitaminas`}>
                    <div className="metric-icon">🥑</div>
                    <div className="metric-label">Grasas</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.fats}g</div>
                  </div>
                </div>

                <div className="grid-2">
                  <div className="card chart-card-overflow">
                    <Plot
                      data={[
                        {
                          type: 'pie',
                          labels: ['Proteínas', 'Carbohidratos', 'Grasas'],
                          values: [
                            analysis.health_plan.nutrition.macronutrients.protein,
                            analysis.health_plan.nutrition.macronutrients.carbs,
                            analysis.health_plan.nutrition.macronutrients.fats
                          ],
                          hole: 0.5,
                          marker: {
                            colors: ['#10b981', '#3b82f6', '#f59e0b']
                          },
                          textinfo: 'label+percent',
                          textfont: {
                            color: '#1e293b'
                          }
                        }
                      ]}
                      layout={getChartLayout('Distribución de Macronutrientes', false, true)}
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div className="card">
                    <h3>💡 Recomendaciones</h3>
                    {analysis.health_plan.nutrition.recommendations?.map((rec, i) => (
                      <div key={i} className="goal-item">✅ {rec}</div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">🍽️</div>
                <h3>Plan de Nutrición</h3>
                <p>Realiza un análisis de salud primero para obtener tu plan personalizado</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'exercise' && (
          <div className="tab-content">
            {analysis?.health_plan?.exercise ? (
              <div>
                <div className="exercise-grid">
                  <div className="card exercise-level-card">
                    <div className="exercise-level-icon">
                      {analysis.fitness_level === 'beginner' ? '🌱' :
                        analysis.fitness_level === 'advanced' ? '🏆' : '💪'}
                    </div>
                    <div className="metric-label">Tu Nivel</div>
                    <div className="metric-value">{analysis.fitness_level}</div>
                  </div>

                  <div className="metrics-grid">
                    <div className="metric-card" title="Actividades cardiovasculares recomendadas para tu nivel">
                      <div className="metric-icon">🏃</div>
                      <div className="metric-label">Cardio</div>
                      <div className="metric-value">{analysis.health_plan.exercise.cardio}</div>
                    </div>
                    <div className="metric-card" title="Ejercicios de fuerza y tonificación muscular">
                      <div className="metric-icon">🏋️</div>
                      <div className="metric-label">Fuerza</div>
                      <div className="metric-value">{analysis.health_plan.exercise.strength}</div>
                    </div>
                    <div className="metric-card" title="Rutinas de estiramientos y flexibilidad">
                      <div className="metric-icon">🧘</div>
                      <div className="metric-label">Flexibilidad</div>
                      <div className="metric-value">{analysis.health_plan.exercise.flexibility}</div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3>🗓️ Plan Semanal</h3>
                  <div className="exercise-chart-container">
                    <Plot
                      data={[
                        {
                          x: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
                          y: [30, 45, 20, 60, 30, 45, 0],
                          type: 'bar',
                          marker: {
                            color: ['#10b981', '#3b82f6', '#f59e0b', '#10b981', '#3b82f6', '#10b981', '#cbd5e1']
                          }
                        }
                      ]}
                      layout={getChartLayout('Rutina Semanal Recomendada', true)}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">💪</div>
                <h3>Plan de Ejercicio</h3>
                <p>Realiza un análisis de salud primero para obtener tu rutina personalizada</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="tab-content">
            {analysis ? (
              <div>
                <div className="reports-header">
                  <div className="reports-header-inner">
                    <label htmlFor="language-select">Idioma del Reporte:</label>
                    <select
                      id="language-select"
                      value={reportLanguage}
                      onChange={(e) => setReportLanguage(e.target.value)}
                    >
                      <option value="es">Español</option>
                      <option value="en">English</option>
                    </select>
                  </div>
                </div>

                <div className="grid-2">
                  <div className="report-card">
                    <div className="report-card-header">
                      <h3>🏥 Estado General de Salud</h3>
                      <p>Resumen clínico completo para compartir con tu médico.</p>
                    </div>
                    <div className="report-card-buttons">
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/health/pdf', reportLanguage === 'es' ? 'reporte_salud.pdf' : 'health_report.pdf')}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/health/excel', reportLanguage === 'es' ? 'reporte_salud.xlsx' : 'health_report.xlsx')}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/health/word', reportLanguage === 'es' ? 'reporte_salud.docx' : 'health_report.docx')}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>

                  <div className="report-card">
                    <div className="report-card-header">
                      <h3>📊 Resumen de Predicciones</h3>
                      <p>Progreso de peso y predicciones a 6 meses.</p>
                    </div>
                    <div className="report-card-buttons">
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/predictions/pdf', reportLanguage === 'es' ? 'reporte_predicciones.pdf' : 'predictions_report.pdf')}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/predictions/excel', reportLanguage === 'es' ? 'reporte_predicciones.xlsx' : 'predictions_report.xlsx')}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/predictions/word', reportLanguage === 'es' ? 'reporte_predicciones.docx' : 'predictions_report.docx')}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>

                  <div className="report-card">
                    <div className="report-card-header">
                      <h3>🥗 Recetas Sugeridas</h3>
                      <p>Plan de alimentación personalizado.</p>
                    </div>
                    <div className="report-card-buttons">
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/recipes/pdf', reportLanguage === 'es' ? 'reporte_recetas.pdf' : 'recipes_report.pdf')}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/recipes/excel', reportLanguage === 'es' ? 'reporte_recetas.xlsx' : 'recipes_report.xlsx')}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/recipes/word', reportLanguage === 'es' ? 'reporte_recetas.docx' : 'recipes_report.docx')}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>

                  <div className="report-card">
                    <div className="report-card-header">
                      <h3>💪 Plan de Ejercicio</h3>
                      <p>Rutina adaptada a tu nivel de actividad.</p>
                    </div>
                    <div className="report-card-buttons">
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/exercise/pdf', reportLanguage === 'es' ? 'reporte_ejercicio.pdf' : 'exercise_report.pdf')}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/exercise/excel', reportLanguage === 'es' ? 'reporte_ejercicio.xlsx' : 'exercise_report.xlsx')}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/exercise/word', reportLanguage === 'es' ? 'reporte_ejercicio.docx' : 'exercise_report.docx')}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">📑</div>
                <h3>Reportes</h3>
                <p>Realiza un análisis de salud primero para generar tus reportes personalizados</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="tab-content">
            {loading ? (
              <div className="empty-state">
                <div className="empty-state-icon small">⏳</div>
                <h3>Cargando predicciones...</h3>
              </div>
            ) : (() => {
              const predData = latestPrediction || (analysis && analysis.predictions ? {
                profile_snapshot: {
                  weight: analysis.bmi * ((analysis.bmi < 18.5 ? 170 : (analysis.bmi < 25 ? 175 : 180)) / 100) ** 2,
                  height: analysis.bmi < 18.5 ? 170 : (analysis.bmi < 25 ? 175 : 180)
                },
                predictions_data: analysis.predictions.predictions_data
              } : null);

              return predData ? (
                <div>
                  {analysis?.ml_prediction?.predicted_class && (
                    <div className="ml-prediction-card">
                      <div className="ml-prediction-header">
                        <span className="ml-prediction-icon">🤖</span>
                        <h3>Clasificación ML (XGBoost)</h3>
                      </div>
                      <div className="ml-prediction-body">
                        <div className="ml-prediction-main">
                          <div className="ml-predicted-class">
                            <span className="ml-label">Categoría Predicha</span>
                            <span className="ml-value">{analysis.ml_prediction.predicted_class.replace(/_/g, ' ')}</span>
                          </div>
                          <div className="ml-confidence">
                            <span className="ml-label">Confianza</span>
                            <div className="ml-confidence-bar-container">
                              <div className="ml-confidence-bar" style={{ width: `${analysis.ml_prediction.confidence}%` }}></div>
                            </div>
                            <span className="ml-confidence-text">{analysis.ml_prediction.confidence.toFixed(1)}%</span>
                          </div>
                        </div>
                        <div className="ml-prediction-details">
                          <span className="ml-model-badge">{analysis.ml_prediction.model_used}</span>
                          <span className="ml-inference-time">{analysis.ml_prediction.inference_time_ms.toFixed(2)}ms</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {analysis?.xai && (
                    <div className="xai-section">
                      {/* ¿Por qué la IA tomó esta decisión? */}
                      <div className="xai-card xai-card-explanation">
                        <div className="xai-card-header">
                          <span className="xai-card-icon">💡</span>
                          <h3>¿Por qué la IA tomó esta decisión?</h3>
                        </div>
                        <div className="xai-card-body">
                          <p className="xai-summary">{analysis.xai.summary}</p>
                          <p className="xai-main-reason">{analysis.xai.main_reason}</p>
                        </div>
                      </div>

                      {/* Nivel de confianza */}
                      <div className="xai-card xai-card-confidence">
                        <div className="xai-card-header">
                          <span className="xai-card-icon">🎯</span>
                          <h3>Nivel de Confianza</h3>
                        </div>
                        <div className="xai-card-body">
                          <p className="xai-confidence-text">{analysis.xai.confidence_text}</p>
                          {analysis.ml_prediction?.predicted_class && (
                            <div className="xai-confidence-meter">
                              <div className="xai-confidence-bar-bg">
                                <div
                                  className="xai-confidence-bar-fill"
                                  style={{
                                    width: `${analysis.ml_prediction.confidence}%`,
                                    background: analysis.ml_prediction.confidence >= 95
                                      ? 'var(--secondary)' : analysis.ml_prediction.confidence >= 80
                                      ? 'var(--primary)' : analysis.ml_prediction.confidence >= 60
                                      ? 'var(--accent)' : 'var(--danger)',
                                  }}
                                />
                              </div>
                              <span className="xai-confidence-value">
                                {analysis.ml_prediction.confidence.toFixed(1)}%
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Factores más importantes */}
                      {analysis.xai.important_features?.length > 0 && (
                        <div className="xai-card xai-card-features">
                          <div className="xai-card-header">
                            <span className="xai-card-icon">📊</span>
                            <h3>Factores Más Importantes</h3>
                          </div>
                          <div className="xai-card-body">
                            {analysis.xai.important_features.map((feat, i) => (
                              <div className="xai-feature-row" key={i}>
                                <span className="xai-feature-name">{feat.display_name}</span>
                                <div className="xai-feature-bar-container">
                                  <div
                                    className="xai-feature-bar"
                                    style={{ width: `${Math.max(feat.importance * 100 * 1.3, 2)}%` }}
                                  />
                                </div>
                                <span className={`xai-feature-badge xai-feature-${feat.level}`}>
                                  {feat.level === 'high' ? 'Alto' : feat.level === 'medium' ? 'Medio' : 'Bajo'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Interpretación clínica */}
                      <div className="xai-card xai-card-clinical">
                        <div className="xai-card-header">
                          <span className="xai-card-icon">🩺</span>
                          <h3>Interpretación Clínica</h3>
                        </div>
                        <div className="xai-card-body">
                          <p>{analysis.xai.risk_explanation}</p>
                          {analysis.xai.recommendations?.length > 0 && (
                            <div className="xai-recommendations">
                              <strong>Recomendaciones:</strong>
                              <ul>
                                {analysis.xai.recommendations.map((rec, i) => (
                                  <li key={i}>{rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Escenarios futuros */}
                      <div className="xai-scenarios-grid">
                        {analysis.xai.scenario_follow && (
                          <div className="xai-card xai-card-scenario xai-card-follow">
                            <div className="xai-card-header">
                              <span className="xai-card-icon">✅</span>
                              <h3>{analysis.xai.scenario_follow.title}</h3>
                            </div>
                            <div className="xai-card-body">
                              <div className="xai-scenario-metrics">
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">Peso proyectado</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_follow.projected_weight_kg} kg</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">IMC proyectado</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_follow.projected_bmi}</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">Categoría esperada</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_follow.projected_category}</span>
                                </div>
                              </div>
                              <p className="xai-scenario-text">{analysis.xai.scenario_follow.evolution_text}</p>
                            </div>
                          </div>
                        )}

                        {analysis.xai.scenario_ignore && (
                          <div className="xai-card xai-card-scenario xai-card-ignore">
                            <div className="xai-card-header">
                              <span className="xai-card-icon">⚠️</span>
                              <h3>{analysis.xai.scenario_ignore.title}</h3>
                            </div>
                            <div className="xai-card-body">
                              <div className="xai-scenario-metrics">
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">Peso estimado</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_ignore.projected_weight_kg} kg</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">IMC estimado</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_ignore.projected_bmi}</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">Categoría estimada</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_ignore.projected_category}</span>
                                </div>
                              </div>
                              <p className="xai-scenario-text">{analysis.xai.scenario_ignore.risk_text}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="prediction-card">
                    <h3>📊 Última Predicción</h3>
                    <div className="metrics-grid">
                      <div className="metric-card" title="Tu peso actual al momento del análisis">
                        <div className="metric-icon">📈</div>
                        <div className="metric-label">Peso Inicial</div>
                        <div className="metric-value">{Math.round(predData.profile_snapshot?.weight * 10) / 10} kg</div>
                      </div>
                      <div className="metric-card" title="Peso proyectado a 2 semanas según el modelo predictivo">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">2 Semanas</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['2_weeks']?.weight_kg} kg
                        </div>
                      </div>
                      <div className="metric-card" title="Peso proyectado a 1 mes según el modelo predictivo">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">1 Mes</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['1_month']?.weight_kg} kg
                        </div>
                      </div>
                      <div className="metric-card" title="Peso proyectado a 6 meses según el modelo predictivo">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">6 Meses</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['6_months']?.weight_kg} kg
                        </div>
                      </div>
                    </div>

                    <div className="prediction-chart-container">
                      <Plot
                        data={[
                          {
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Predicción',
                            x: ['Actual', '2 Semanas', '1 Mes', '6 Meses'],
                            y: [
                              Math.round(predData.profile_snapshot?.weight * 10) / 10,
                              predData.predictions_data?.predictions?.['2_weeks']?.weight_kg,
                              predData.predictions_data?.predictions?.['1_month']?.weight_kg,
                              predData.predictions_data?.predictions?.['6_months']?.weight_kg
                            ],
                            marker: { color: '#3b82f6', size: 10 },
                            line: { color: '#3b82f6', width: 3 }
                          }
                        ]}
                        layout={getChartLayout('Proyección de Peso', true)}
                        style={{ width: '100%' }}
                      />
                    </div>
                  </div>

                  {timelineData?.has_predictions && (
                    <div className="prediction-card">
                      <h3>📅 Progreso Real vs Predicción</h3>
                      {timelineData.actual_progress && timelineData.actual_progress.length > 0 ? (
                        <Plot
                          data={[
                            {
                              type: 'scatter',
                              mode: 'lines+markers',
                              name: 'Predicción',
                              x: ['Inicio', '2 Semanas', '1 Mes', '6 Meses'],
                              y: [
                                Math.round(predData.profile_snapshot?.weight * 10) / 10,
                                predData.predictions_data?.predictions?.['2_weeks']?.weight_kg,
                                predData.predictions_data?.predictions?.['1_month']?.weight_kg,
                                predData.predictions_data?.predictions?.['6_months']?.weight_kg
                              ],
                              marker: { color: '#3b82f6', size: 10 },
                              line: { color: '#3b82f6', width: 2 }
                            },
                            {
                              type: 'scatter',
                              mode: 'lines+markers',
                              name: 'Progreso Real',
                              x: timelineData.actual_progress.map(p => new Date(p.date).toLocaleDateString('es-ES')),
                              y: timelineData.actual_progress.map(p => p.weight_kg),
                              marker: { color: '#10b981', size: 10 },
                              line: { color: '#10b981', width: 2 }
                            }
                          ]}
                          layout={getChartLayout('Comparación: Predicción vs Real', true)}
                          style={{ width: '100%' }}
                        />
                      ) : (
                        <div className="empty-state prediction-empty">
                          <p>No hay progreso registrado aún. Agrega registros diarios para ver la comparación!</p>
                        </div>
                      )}
                    </div>
                  )}

                  {statsData?.has_stats && (
                    <div className="grid-2">
                      <div className="card">
                        <h3>🎯 Precisión de Predicciones</h3>
                        <div className="prediction-stat-center">
                          <div className="prediction-accuracy-value">
                            {statsData.average_accuracy}%
                          </div>
                          <div className="prediction-accuracy-label">Precisión promedio</div>
                        </div>
                      </div>
                      <div className="card">
                        <h3>📊 Historial de Predicciones</h3>
                        {statsData.details?.map((stat, i) => (
                          <div key={i} className="goal-item">
                            <div>
                              <div className="prediction-stat-value">
                                {new Date(stat.date).toLocaleDateString('es-ES')}
                              </div>
                              {stat.accuracy?.['2_weeks'] && (
                                <div className="prediction-stat-detail">
                                  2 Semanas: {stat.accuracy['2_weeks'].accuracy_pct}%
                                </div>
                              )}
                              {stat.accuracy?.['1_month'] && (
                                <div className="prediction-stat-detail">
                                  1 Mes: {stat.accuracy['1_month'].accuracy_pct}%
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              ) : (
                <div className="empty-state">
                  <div className="empty-state-icon">📈</div>
                  <h3>Predicciones de Salud</h3>
                  <p>Realiza un análisis de salud primero para generar predicciones personalizadas!</p>
                </div>
              );
            })()}

          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
