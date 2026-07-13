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
      health_goals: selectedGoals
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



  // Light theme chart layout
  const getChartLayout = (title, isBar = false, isPie = false) => {
    if (isPie) {
      return {
        title: { text: title, font: { color: '#1e293b', size: 16, family: 'Inter, sans-serif' } },
        paper_bgcolor: 'rgba(255,255,255,0)',
        plot_bgcolor: 'rgba(255,255,255,0)',
        height: 400,
        margin: { t: 50, b: 20, l: 20, r: 20 },
        font: { color: '#475569', family: 'Inter, sans-serif' },
        showlegend: true,
        legend: {
          x: 0.5,
          y: -0.2,
          xanchor: 'center',
          orientation: 'h'
        }
      };
    }
    return {
      title: { text: title, font: { color: '#1e293b', size: 16, family: 'Inter, sans-serif' } },
      paper_bgcolor: 'rgba(255,255,255,0)',
      plot_bgcolor: 'rgba(255,255,255,0)',
      height: 400,
      margin: { t: 50, b: 60, l: 60, r: 30 },
      font: { color: '#475569', family: 'Inter, sans-serif' },
      xaxis: {
        tickfont: { color: '#475569' },
        gridcolor: '#e2e8f0'
      },
      yaxis: {
        tickfont: { color: '#475569' },
        gridcolor: '#e2e8f0'
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
            {message.text}
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="tab-content">
            {/* FIX ESTÉTICO: alignItems: 'start' evita que la columna derecha
                se estire para igualar la altura del formulario de la izquierda */}
            <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', marginBottom: '32px', alignItems: 'start' }}>
              <div>
                <div className="profile-section">
                  <h3>📝 Mi Perfil</h3>
                  <form key={profile ? 'loaded' : 'new'} onSubmit={saveProfile} className="profile-form" id="profileForm">
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

                <div style={{ marginTop: '16px' }}>
                  <button
                    type="submit"
                    form="profileForm"
                    className="btn-primary btn-large"
                    disabled={loading}
                  >
                    🤖 Analizar mi Salud
                  </button>
                </div>
              </div>

              {/* FIX ESTÉTICO: position sticky para que este panel se mantenga
                  visible mientras se scrollea el formulario largo de la izquierda,
                  en vez de dejar un hueco blanco debajo */}
              <div style={{ position: 'sticky', top: '20px' }}>
                {analysis ? (
                  <div>
                    <div className="header-section" style={{ marginTop: '0px', marginBottom: '20px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                        {/* Tarjeta 1: Score */}
                        <div style={{ 
                          backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', 
                          padding: '20px', textAlign: 'center', borderBottom: `4px solid ${analysis.health_score < 40 ? '#e74c3c' : analysis.health_score <= 60 ? '#e67e22' : analysis.health_score <= 80 ? '#f1c40f' : '#2ecc71'}` 
                        }}>
                          <div style={{ color: '#7f8c8d', fontSize: '1.1rem', fontWeight: '600', marginBottom: '10px' }}>Health Score</div>
                          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: analysis.health_score < 40 ? '#e74c3c' : analysis.health_score <= 60 ? '#e67e22' : analysis.health_score <= 80 ? '#f1c40f' : '#2ecc71' }}>
                            {analysis.health_score}<span style={{fontSize: '1.2rem'}}>/100</span>
                          </div>
                          <div style={{ fontSize: '0.9rem', color: '#95a5a6', marginTop: '5px' }}>Puntuación penalizada</div>
                        </div>

                        {/* Tarjeta 2: BMI */}
                        <div style={{ backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '20px', textAlign: 'center' }}>
                          <div style={{ color: '#7f8c8d', fontSize: '1.1rem', fontWeight: '600', marginBottom: '10px' }}>Índice Masa Corporal</div>
                          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#3498db' }}>{analysis.bmi}</div>
                          <div style={{ fontSize: '0.9rem', color: '#95a5a6', marginTop: '5px' }}>Categoría: {analysis.bmi_category.replace('_', ' ').toUpperCase()}</div>
                        </div>

                        {/* Tarjeta 3: Calorías */}
                        <div style={{ backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '20px', textAlign: 'center' }}>
                          <div style={{ color: '#7f8c8d', fontSize: '1.1rem', fontWeight: '600', marginBottom: '10px' }}>Calorías Sugeridas</div>
                          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#9b59b6' }}>{analysis.tdee?.toFixed(0)}</div>
                          <div style={{ fontSize: '0.9rem', color: '#95a5a6', marginTop: '5px' }}>kcal/día adaptadas a objetivo</div>
                        </div>

                      </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                      <div style={{ backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '20px', borderLeft: '5px solid #e74c3c', height: '100%' }}>
                        <h3 style={{ color: '#2c3e50', marginTop: 0 }}>Atención Médica y Alertas</h3>
                        <div style={{ marginTop: '15px' }}>
                          {analysis.alerts && analysis.alerts.length > 0 ? (
                            analysis.alerts.map((alert, i) => (
                              <p key={i} style={{ marginBottom: '8px', color: '#333' }}>
                                {alert.priority === 'high' || alert.message.includes('Clínica') ? '🚨' : '⚠️'} {alert.message}
                              </p>
                            ))
                          ) : (
                            <p style={{ color: '#333' }}>✅ No tienes alertas médicas críticas en este momento.</p>
                          )}
                        </div>
                      </div>

                      <div style={{ backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '20px', borderLeft: '5px solid #3498db', height: '100%' }}>
                        <h3 style={{ color: '#2c3e50', marginTop: 0 }}>Objetivos Semanales</h3>
                        <div style={{ marginTop: '15px' }}>
                          {analysis.weekly_goals && analysis.weekly_goals.length > 0 ? (
                            analysis.weekly_goals.map((goal, i) => (
                              <p key={i} style={{ marginBottom: '8px', color: '#333' }}>🎯 {goal}</p>
                            ))
                          ) : (
                            <p style={{ color: '#333' }}>No hay objetivos asignados.</p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Charts Section */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginTop: '20px' }}>
                      <div style={{ backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '20px', overflow: 'hidden' }}>
                        <h3 style={{ color: '#2c3e50', marginTop: 0 }}>Comparativa de Health Score</h3>
                        <Plot
                          data={[
                            {
                              type: 'bar',
                              name: 'Tu Puntuación',
                              x: ['Health Score'],
                              y: [analysis.health_score],
                              marker: {
                                color: analysis.health_score < 40 ? '#e74c3c' : analysis.health_score <= 60 ? '#e67e22' : analysis.health_score <= 80 ? '#f1c40f' : '#2ecc71'
                              }
                            },
                            {
                              type: 'bar',
                              name: 'Promedio Población',
                              x: ['Health Score'],
                              y: [(profile?.age || 30) < 40 ? 75 : 65],
                              marker: { color: '#3498db' }
                            }
                          ]}
                          layout={getChartLayout('Comparativa de Health Score', true)}
                          style={{ width: '100%' }}
                        />
                      </div>

                      <div style={{ backgroundColor: '#fff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', padding: '20px', overflow: 'hidden' }}>
                        <h3 style={{ color: '#2c3e50', marginTop: 0 }}>Distribución de Macronutrientes</h3>
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
                          <p style={{ color: '#64748b', textAlign: 'center', padding: '40px 0' }}>
                            No hay datos de macronutrientes disponibles.
                          </p>
                        )}
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="empty-state">
                    <div style={{ fontSize: '5rem', marginBottom: '20px' }}>📋</div>
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
                <div className="metrics-grid" style={{ marginBottom: '24px' }}>
                  <div className="metric-card">
                    <div className="metric-icon">🔥</div>
                    <div className="metric-label">Calorías Diarias</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.daily_calories}</div>
                    <div className="metric-desc">kcal</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon">🥩</div>
                    <div className="metric-label">Proteínas</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.protein}g</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon">🍚</div>
                    <div className="metric-label">Carbohidratos</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.carbs}g</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-icon">🥑</div>
                    <div className="metric-label">Grasas</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.fats}g</div>
                  </div>
                </div>

                <div className="grid-2">
                  <div className="card" style={{ overflow: 'hidden' }}>
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
                <div style={{ fontSize: '5rem', marginBottom: '20px' }}>🍽️</div>
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
                <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: '24px', marginBottom: '24px' }}>
                  <div className="card" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '12px' }}>
                      {analysis.fitness_level === 'beginner' ? '🌱' :
                        analysis.fitness_level === 'advanced' ? '🏆' : '💪'}
                    </div>
                    <div className="metric-label">Tu Nivel</div>
                    <div className="metric-value">{analysis.fitness_level}</div>
                  </div>

                  <div className="metrics-grid">
                    <div className="metric-card">
                      <div className="metric-icon">🏃</div>
                      <div className="metric-label">Cardio</div>
                      <div className="metric-value">{analysis.health_plan.exercise.cardio}</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-icon">🏋️</div>
                      <div className="metric-label">Fuerza</div>
                      <div className="metric-value">{analysis.health_plan.exercise.strength}</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-icon">🧘</div>
                      <div className="metric-label">Flexibilidad</div>
                      <div className="metric-value">{analysis.health_plan.exercise.flexibility}</div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3>🗓️ Plan Semanal</h3>
                  <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
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
                <div style={{ fontSize: '5rem', marginBottom: '20px' }}>💪</div>
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
                <div style={{ marginBottom: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <label htmlFor="language-select" style={{ color: 'var(--text-muted)' }}>Idioma del Reporte:</label>
                      <select
                        id="language-select"
                        value={reportLanguage}
                        onChange={(e) => setReportLanguage(e.target.value)}
                        style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                      >
                        <option value="es">Español</option>
                        <option value="en">English</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="grid-2">
                  {/* Reporte 1: Estado General de Salud */}
                  <div className="card">
                    <div style={{ marginBottom: '20px' }}>
                      <h3>🏥 Estado General de Salud</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Resumen clínico completo para compartir con tu médico.
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/health/pdf', reportLanguage === 'es' ? 'reporte_salud.pdf' : 'health_report.pdf')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/health/excel', reportLanguage === 'es' ? 'reporte_salud.xlsx' : 'health_report.xlsx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/health/word', reportLanguage === 'es' ? 'reporte_salud.docx' : 'health_report.docx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>

                  {/* Reporte 2: Resumen de Predicciones */}
                  <div className="card">
                    <div style={{ marginBottom: '20px' }}>
                      <h3>📊 Resumen de Predicciones</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Progreso de peso y predicciones a 6 meses.
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/predictions/pdf', reportLanguage === 'es' ? 'reporte_predicciones.pdf' : 'predictions_report.pdf')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/predictions/excel', reportLanguage === 'es' ? 'reporte_predicciones.xlsx' : 'predictions_report.xlsx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/predictions/word', reportLanguage === 'es' ? 'reporte_predicciones.docx' : 'predictions_report.docx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>

                  {/* Reporte 3: Recetas Sugeridas */}
                  <div className="card">
                    <div style={{ marginBottom: '20px' }}>
                      <h3>🥗 Recetas Sugeridas</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Plan de alimentación personalizado.
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/recipes/pdf', reportLanguage === 'es' ? 'reporte_recetas.pdf' : 'recipes_report.pdf')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/recipes/excel', reportLanguage === 'es' ? 'reporte_recetas.xlsx' : 'recipes_report.xlsx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/recipes/word', reportLanguage === 'es' ? 'reporte_recetas.docx' : 'recipes_report.docx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>

                  {/* Reporte 4: Plan de Ejercicio */}
                  <div className="card">
                    <div style={{ marginBottom: '20px' }}>
                      <h3>💪 Plan de Ejercicio</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Rutina adaptada a tu nivel de actividad.
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/exercise/pdf', reportLanguage === 'es' ? 'reporte_ejercicio.pdf' : 'exercise_report.pdf')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 PDF
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/exercise/excel', reportLanguage === 'es' ? 'reporte_ejercicio.xlsx' : 'exercise_report.xlsx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Excel
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => downloadReport('/api/reports/exercise/word', reportLanguage === 'es' ? 'reporte_ejercicio.docx' : 'exercise_report.docx')}
                        style={{ padding: '8px 16px', fontSize: '0.9rem' }}
                      >
                        📥 Word
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div style={{ fontSize: '5rem', marginBottom: '20px' }}>📑</div>
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
                <div style={{ fontSize: '3rem', marginBottom: '20px' }}>⏳</div>
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
                  {/* Latest Prediction */}
                  <div className="card" style={{ marginBottom: '24px' }}>
                    <h3>📊 Última Predicción</h3>
                    <div className="metrics-grid">
                      <div className="metric-card">
                        <div className="metric-icon">📈</div>
                        <div className="metric-label">Peso Inicial</div>
                        <div className="metric-value">{Math.round(predData.profile_snapshot?.weight * 10) / 10} kg</div>
                      </div>
                      <div className="metric-card">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">2 Semanas</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['2_weeks']?.weight_kg} kg
                        </div>
                      </div>
                      <div className="metric-card">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">1 Mes</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['1_month']?.weight_kg} kg
                        </div>
                      </div>
                      <div className="metric-card">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">6 Meses</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['6_months']?.weight_kg} kg
                        </div>
                      </div>
                    </div>

                    <div style={{ marginTop: '20px' }}>
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

                  {/* Timeline & Actual Progress */}
                  {timelineData?.has_predictions && (
                    <div className="card" style={{ marginBottom: '24px' }}>
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
                        <div className="empty-state" style={{ padding: '40px 20px' }}>
                          <p>No hay progreso registrado aún. Agrega registros diarios para ver la comparación!</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Stats */}
                  {statsData?.has_stats && (
                    <div className="grid-2">
                      <div className="card">
                        <h3>🎯 Precisión de Predicciones</h3>
                        <div style={{ textAlign: 'center', padding: '20px' }}>
                          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#3b82f6' }}>
                            {statsData.average_accuracy}%
                          </div>
                          <div style={{ color: '#64748b', marginTop: '8px' }}>Precisión promedio</div>
                        </div>
                      </div>
                      <div className="card">
                        <h3>📊 Historial de Predicciones</h3>
                        {statsData.details?.map((stat, i) => (
                          <div key={i} className="goal-item">
                            <div>
                              <div style={{ fontWeight: 'bold' }}>
                                {new Date(stat.date).toLocaleDateString('es-ES')}
                              </div>
                              {stat.accuracy?.['2_weeks'] && (
                                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
                                  2 Semanas: {stat.accuracy['2_weeks'].accuracy_pct}%
                                </div>
                              )}
                              {stat.accuracy?.['1_month'] && (
                                <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
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
                  <div style={{ fontSize: '5rem', marginBottom: '20px' }}>📈</div>
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