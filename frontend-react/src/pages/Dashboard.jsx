import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { useTranslation } from 'react-i18next';
import Plot from 'react-plotly.js';
import LanguageSwitcher from '../components/LanguageSwitcher';
import ThemeToggle from '../components/ThemeToggle';
import ExplainabilityCenter from '../components/ExplainabilityCenter';
import HealthAssistant from '../components/HealthAssistant';
import './Dashboard.css';

function Dashboard() {
  const { token, user, logout } = useAuth();
  const { apiRequest } = useApi();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [profile, setProfile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [latestPrediction, setLatestPrediction] = useState(null);
  const [predictionsHistory, setPredictionsHistory] = useState(null);
  const [timelineData, setTimelineData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [importanceData, setImportanceData] = useState(null);
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
      const importance = await fetch('/eda/models/importance.json').then(r => r.ok ? r.json() : null).catch(() => null);
      if (importance) setImportanceData(importance);
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
      setMessage({ type: 'success', text: t('messages.profileSaved') });
      await analyzeHealth();
    } else {
      setMessage({ type: 'error', text: result.error });
    }
    setLoading(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const analyzeHealth = async () => {
    setLoading(true);
    setMessage({ type: 'info', text: t('messages.analyzing') });

    const result = await apiRequest('/api/analyze', 'POST', null, token);

    if (result.success) {
      setAnalysis(result.data);
      setMessage({ type: 'success', text: t('messages.analysisComplete') });
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
    if (score >= 80) return t('analysis.excellent');
    if (score >= 60) return t('analysis.good');
    return t('analysis.improvable');
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
            🏥 {t('app.title')}
          </div>
          <div className="sidebar-controls">
            <LanguageSwitcher />
            <ThemeToggle />
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
            📊 {t('nav.dashboard')}
          </button>
          <button
            className={`nav-item ${activeTab === 'nutrition' ? 'active' : ''}`}
            onClick={() => setActiveTab('nutrition')}
          >
            🥗 {t('nav.nutrition')}
          </button>
          <button
            className={`nav-item ${activeTab === 'exercise' ? 'active' : ''}`}
            onClick={() => setActiveTab('exercise')}
          >
            💪 {t('nav.exercise')}
          </button>
          <button
            className={`nav-item ${activeTab === 'predictions' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('predictions');
              loadPredictions();
            }}
          >
            📈 {t('nav.predictions')}
          </button>
          <button
            className={`nav-item ${activeTab === 'explainability' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('explainability');
              loadPredictions();
            }}
          >
            🔍 {t('nav.explainability')}
          </button>
          <button
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('reports');
              loadPredictions();
            }}
          >
            📑 {t('nav.reports')}
          </button>
        </nav>

        <button className="btn-logout" onClick={logout}>
          🚪 {t('nav.logout')}
        </button>
      </aside>

      <main className="main-content">
        <h1 className="page-title">{t('app.subtitle')}</h1>
        <p className="page-subtitle">{t('app.description')}</p>

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
                  <h3>📝 {t('profile.title')}</h3>
                  <form key={profile ? 'loaded' : 'new'} onSubmit={saveProfile} className="profile-form" id="profileForm">
                    <div className="form-section-title">{t('profile.personalData')}</div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>{t('profile.age')}</label>
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
                        <label>{t('profile.weight')}</label>
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
                        <label>{t('profile.height')}</label>
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
                        <label>{t('profile.gender')}</label>
                        <select name="gender" defaultValue={profile?.gender || ''} required>
                          <option value="" disabled>{t('profile.choose')}</option>
                          <option value="male">{t('profile.male')}</option>
                          <option value="female">{t('profile.female')}</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-section-title">{t('profile.lifestyle')}</div>
                    <div className="form-group">
                      <label>{t('profile.activityLevel')}</label>
                      <select name="activityLevel" defaultValue={profile?.activity_level || ''} required>
                        <option value="" disabled>{t('profile.choose')}</option>
                        <option value="sedentary">{t('profile.sedentary')}</option>
                        <option value="light">{t('profile.light')}</option>
                        <option value="moderate">{t('profile.moderate')}</option>
                        <option value="active">{t('profile.active')}</option>
                        <option value="very_active">{t('profile.veryActive')}</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>{t('profile.sleepHours')}: {sleepHours}</label>
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
                      <label>{t('profile.geneticRisk')}</label>
                      <select name="geneticsRisk" defaultValue={profile?.genetics_risk || 'low'}>
                        <option value="low">{t('profile.geneticLow')}</option>
                        <option value="medium">{t('profile.geneticMedium')}</option>
                        <option value="high">{t('profile.geneticHigh')}</option>
                      </select>
                    </div>

                    <div className="form-section-title">{t('profile.health')}</div>
                    <div className="form-check">
                      <input type="checkbox" name="smokes" defaultChecked={profile?.smokes} id="smokes" />
                      <label htmlFor="smokes">{t('profile.smoker')}</label>
                    </div>

                    <div className="form-check">
                      <input type="checkbox" name="hasChronic" defaultChecked={profile?.has_chronic_conditions} id="hasChronic" onChange={(e) => {
                        const detailInput = document.getElementById('chronicDetailContainer');
                        if (detailInput) detailInput.style.display = e.target.checked ? 'block' : 'none';
                      }} />
                      <label htmlFor="hasChronic">{t('profile.chronicConditions')}</label>
                    </div>

                    <div className="form-group" id="chronicDetailContainer" style={{ display: profile?.has_chronic_conditions ? 'block' : 'none', marginTop: '10px' }}>
                      <label>{t('profile.chronicDetail')}</label>
                      <input type="text" name="chronicDetail" defaultValue={profile?.chronic_conditions_detail || ''} placeholder={t('profile.chronicPlaceholder')} />
                    </div>

                    <div className="form-check">
                      <input type="checkbox" name="familyHistory" defaultChecked={profile?.family_history} id="familyHistory" />
                      <label htmlFor="familyHistory">{t('profile.familyHistory')}</label>
                    </div>

                    <div className="form-section-title">{t('profile.nutritionSection')}</div>
                    <div className="form-group">
                      <label>{t('profile.fastFood')}</label>
                      <select name="favc" defaultValue={profile?.favc || 'Sometimes'}>
                        <option value="Always">{t('profile.fastFoodAlways')}</option>
                        <option value="Frequently">{t('profile.fastFoodFrequently')}</option>
                        <option value="Sometimes">{t('profile.fastFoodSometimes')}</option>
                        <option value="No">{t('profile.fastFoodNo')}</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>{t('profile.vegetables')}</label>
                      <select name="fcvc" defaultValue={profile?.fcvc || 2.0}>
                        <option value="1">{t('profile.veg1')}</option>
                        <option value="2">{t('profile.veg2')}</option>
                        <option value="3">{t('profile.veg3')}</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>{t('profile.water')}</label>
                      <select name="ch2o" defaultValue={profile?.ch2o || 2.0}>
                        <option value="1">{t('profile.water1')}</option>
                        <option value="2">{t('profile.water2')}</option>
                        <option value="3">{t('profile.water3')}</option>
                      </select>
                    </div>

                    <div className="form-section-title">{t('profile.goalsSection')}</div>
                    <div className="form-group">
                      <label>{t('profile.healthGoals')}</label>
                      <select name="healthGoals" multiple defaultValue={profile?.health_goals || []} size="6" required>
                        <option value="weight_loss">{t('goals.weightLoss')}</option>
                        <option value="muscle_gain">{t('goals.muscleGain')}</option>
                        <option value="better_sleep">{t('goals.betterSleep')}</option>
                        <option value="stress_reduction">{t('goals.stressReduction')}</option>
                        <option value="energy_boost">{t('goals.energyBoost')}</option>
                        <option value="general_wellness">{t('goals.generalWellness')}</option>
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
                        {t('profile.analyzing')}
                      </>
                    ) : (
                      t('profile.analyze')
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
                        <div className="analysis-card-label">{t('analysis.healthScore')}</div>
                        <div className="analysis-card-value tooltip-trigger" title="Puntuación de 0 a 100 que refleja tu estado general de salud. Más alto = mejor." style={{ color: getScoreColorVar(analysis.health_score) }}>
                          {analysis.health_score}<span className="score-value-suffix">/100</span>
                        </div>
                        <div className="analysis-card-desc">{t('analysis.healthScoreDesc')}</div>
                        <span className={`analysis-card-badge ${analysis.health_score < 60 ? 'warning' : analysis.health_score >= 80 ? '' : 'info'}`}>
                          {getScoreText(analysis.health_score)}
                        </span>
                      </div>

                      <div className="analysis-card bmi">
                        <div className="analysis-card-icon" title="Índice de Masa Corporal — relación entre tu peso y tu estatura">⚖️</div>
                        <div className="analysis-card-label">{t('analysis.bmi')}</div>
                        <div className="analysis-card-value tooltip-trigger" title={`IMC: ${analysis.bmi} — Categoría: ${analysis.bmi_category.replace('_', ' ')}. Valores normales: 18.5 – 24.9`}>{analysis.bmi}</div>
                        <div className="analysis-card-desc">{t('analysis.bmiDesc')}</div>
                        <span className={`analysis-card-badge ${analysis.bmi_category === 'normal' ? '' : analysis.bmi_category === 'obese' ? 'danger' : 'warning'}`}>
                          {analysis.bmi_category.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="analysis-card calories">
                        <div className="analysis-card-icon" title="Total de Energía Diaria Expendida — calorías que tu cuerpo necesita al día">🔥</div>
                        <div className="analysis-card-label">{t('analysis.dailyCalories')}</div>
                        <div className="analysis-card-value tooltip-trigger" title={`TDEE: ${analysis.tdee?.toFixed(0)} kcal/día. Calculado según tu nivel de actividad, peso, altura y objetivo.`}>{analysis.tdee?.toFixed(0)}</div>
                        <div className="analysis-card-desc">{t('analysis.caloriesDesc')}</div>
                        <span className="analysis-card-badge info">TDEE</span>
                      </div>
                    </div>

                    <div className="analysis-panels">
                      <div className="analysis-panel alerts">
                        <h3>{t('analysis.alerts')}</h3>
                        <p className="analysis-panel-subtitle">{t('analysis.alertsDesc')}</p>
                        <div className="analysis-panel-content">
                          {analysis.alerts && analysis.alerts.length > 0 ? (
                            analysis.alerts.map((alert, i) => (
                              <p key={i}>
                                {alert.priority === 'high' || alert.message.includes('Clínica') ? '🚨' : '⚠️'} {alert.message}
                              </p>
                            ))
                          ) : (
                            <p>{t('analysis.noAlerts')}</p>
                          )}
                        </div>
                      </div>

                      <div className="analysis-panel goals">
                        <h3>{t('analysis.weeklyGoals')}</h3>
                        <p className="analysis-panel-subtitle">{t('analysis.weeklyGoalsDesc')}</p>
                        <div className="analysis-panel-content">
                          {analysis.weekly_goals && analysis.weekly_goals.length > 0 ? (
                            analysis.weekly_goals.map((goal, i) => (
                              <p key={i}>🎯 {goal}</p>
                            ))
                          ) : (
                            <p>{t('analysis.noGoals')}</p>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="analysis-charts">
                      <div className="analysis-chart-card">
                        <h3>{t('analysis.scoreComparison')}</h3>
                        <p className="analysis-chart-card-subtitle">{t('analysis.scoreComparisonSubtitle')}</p>
                        <Plot
                          data={[
                            {
                              type: 'bar',
                              name: t('analysis.yourScore'),
                              x: [t('analysis.healthScore')],
                              y: [analysis.health_score],
                              marker: {
                                color: getScoreColorVar(analysis.health_score)
                              }
                            },
                            {
                              type: 'bar',
                              name: t('analysis.populationAvg'),
                              x: [t('analysis.healthScore')],
                              y: [(profile?.age || 30) < 40 ? 75 : 65],
                              marker: { color: 'var(--info)' }
                            }
                          ]}
                          layout={getChartLayout(t('analysis.scoreComparison'), true)}
                          style={{ width: '100%' }}
                        />
                      </div>

                      <div className="analysis-chart-card">
                        <h3>{t('analysis.macronutrients')}</h3>
                        <p className="analysis-chart-card-subtitle">{t('analysis.macroSubtitle')}</p>
                        {analysis.health_plan?.nutrition?.macronutrients ? (
                          <Plot
                            data={[
                              {
                                type: 'pie',
                                labels: [t('analysis.protein'), t('analysis.carbs'), t('analysis.fats')],
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
                            layout={getChartLayout(t('analysis.macronutrients'), false, true)}
                            style={{ width: '100%' }}
                          />
                        ) : (
                          <p className="analysis-no-data-msg">
                            {t('analysis.noMacroData')}
                          </p>
                        )}
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <h3>{t('analysis.emptyTitle')}</h3>
                    <p>{t('analysis.emptyDesc')}</p>
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
                    <div className="metric-label">{t('nutrition.dailyCalories')}</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.daily_calories}</div>
                    <div className="metric-desc">kcal</div>
                  </div>
                  <div className="metric-card" title={`Proteínas: ${analysis.health_plan.nutrition.macronutrients.protein}g — esenciales para músculo y recuperación`}>
                    <div className="metric-icon">🥩</div>
                    <div className="metric-label">{t('nutrition.protein')}</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.protein}g</div>
                  </div>
                  <div className="metric-card" title={`Carbohidratos: ${analysis.health_plan.nutrition.macronutrients.carbs}g — principal fuente de energía`}>
                    <div className="metric-icon">🍚</div>
                    <div className="metric-label">{t('nutrition.carbs')}</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.carbs}g</div>
                  </div>
                  <div className="metric-card" title={`Grasas: ${analysis.health_plan.nutrition.macronutrients.fats}g — necesarias para hormonas y absorción de vitaminas`}>
                    <div className="metric-icon">🥑</div>
                    <div className="metric-label">{t('nutrition.fats')}</div>
                    <div className="metric-value">{analysis.health_plan.nutrition.macronutrients.fats}g</div>
                  </div>
                </div>

                <div className="grid-2">
                  <div className="card chart-card-overflow">
                    <Plot
                      data={[
                        {
                          type: 'pie',
                          labels: [t('nutrition.protein'), t('nutrition.carbs'), t('nutrition.fats')],
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
                      layout={getChartLayout(t('nutrition.distribution'), false, true)}
                      style={{ width: '100%' }}
                    />
                  </div>

                  <div className="card">
                    <h3>{t('nutrition.recommendations')}</h3>
                    {analysis.health_plan.nutrition.recommendations?.map((rec, i) => (
                      <div key={i} className="goal-item">✅ {rec}</div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">🍽️</div>
                <h3>{t('nutrition.emptyTitle')}</h3>
                <p>{t('nutrition.emptyDesc')}</p>
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
                    <div className="metric-label">{t('exercise.yourLevel')}</div>
                    <div className="metric-value">{analysis.fitness_level}</div>
                  </div>

                  <div className="metrics-grid">
                    <div className="metric-card" title={t('exercise.cardioTooltip')}>
                      <div className="metric-icon">🏃</div>
                      <div className="metric-label">{t('exercise.cardio')}</div>
                      <div className="metric-value">{analysis.health_plan.exercise.cardio}</div>
                    </div>
                    <div className="metric-card" title={t('exercise.strengthTooltip')}>
                      <div className="metric-icon">🏋️</div>
                      <div className="metric-label">{t('exercise.strength')}</div>
                      <div className="metric-value">{analysis.health_plan.exercise.strength}</div>
                    </div>
                    <div className="metric-card" title={t('exercise.flexTooltip')}>
                      <div className="metric-icon">🧘</div>
                      <div className="metric-label">{t('exercise.flexibility')}</div>
                      <div className="metric-value">{analysis.health_plan.exercise.flexibility}</div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3>{t('exercise.weeklyPlan')}</h3>
                  <div className="exercise-chart-container">
                    <Plot
                      data={[
                        {
                          x: [t('days.mon'), t('days.tue'), t('days.wed'), t('days.thu'), t('days.fri'), t('days.sat'), t('days.sun')],
                          y: [30, 45, 20, 60, 30, 45, 0],
                          type: 'bar',
                          marker: {
                            color: ['#10b981', '#3b82f6', '#f59e0b', '#10b981', '#3b82f6', '#10b981', '#cbd5e1']
                          }
                        }
                      ]}
                      layout={getChartLayout(t('exercise.weeklyRoutine'), true)}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">💪</div>
                <h3>{t('exercise.emptyTitle')}</h3>
                <p>{t('exercise.emptyDesc')}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="tab-content">
            {analysis ? (
              <div>
                <div className="reports-summaries">
                  <div className="report-summary-card">
                    <h3>📋 {t('reports.executiveSummary')}</h3>
                    <div className="summary-metrics">
                      <div className="summary-metric">
                        <span className="summary-label">{t('analysis.healthScore')}</span>
                        <span className="summary-value" style={{ color: getScoreColorVar(analysis.health_score) }}>{analysis.health_score}/100</span>
                      </div>
                      <div className="summary-metric">
                        <span className="summary-label">{t('analysis.bmi')}</span>
                        <span className="summary-value">{analysis.bmi}</span>
                      </div>
                      <div className="summary-metric">
                        <span className="summary-label">{t('analysis.tdee')}</span>
                        <span className="summary-value">{analysis.tdee?.toFixed(0)} kcal</span>
                      </div>
                    </div>
                    {analysis.alerts?.length > 0 && (
                      <div className="summary-alerts">
                        <strong>{t('reports.riskFactors')}:</strong>
                        <ul>
                          {analysis.alerts.slice(0, 3).map((alert, i) => (
                            <li key={i}>{alert.message || alert}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {analysis.weekly_goals?.length > 0 && (
                      <div className="summary-goals">
                        <strong>{t('reports.improvements')}:</strong>
                        <ul>
                          {analysis.weekly_goals.slice(0, 3).map((goal, i) => (
                            <li key={i}>{goal}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="report-summary-card">
                    <h3>⚕️ {t('reports.clinicalSummary')}</h3>
                    <div className="summary-metrics">
                      <div className="summary-metric">
                        <span className="summary-label">{t('analysis.bmi')}</span>
                        <span className="summary-value">{analysis.bmi} — {analysis.bmi_category?.replace('_', ' ')}</span>
                      </div>
                      <div className="summary-metric">
                        <span className="summary-label">{t('analysis.dailyCalories')}</span>
                        <span className="summary-value">{analysis.health_plan?.nutrition?.daily_calories || 'N/A'} kcal</span>
                      </div>
                    </div>
                    {analysis.health_plan?.nutrition?.recommendations?.length > 0 && (
                      <div className="summary-recommendations">
                        <strong>{t('reports.improvements')}:</strong>
                        <ul>
                          {analysis.health_plan.nutrition.recommendations.slice(0, 3).map((rec, i) => (
                            <li key={i}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="report-summary-card report-summary-ai">
                    <h3>🤖 {t('reports.aiSummary')}</h3>
                    {analysis.xai ? (
                      <div className="ai-summary-content">
                        <p className="ai-summary-main-reason"><strong>{t('xai.mainReason')}:</strong> {analysis.xai.main_reason}</p>
                        <p className="ai-summary-risk">{analysis.xai.risk_explanation}</p>
                        {analysis.ml_prediction && (
                          <div className="ai-summary-ml">
                            <span className="ml-badge">{analysis.ml_prediction.model_used}</span>
                            <span className="ml-confidence-inline">{t('predictions.confidence')}: {analysis.ml_prediction.confidence?.toFixed(1)}%</span>
                          </div>
                        )}
                        {analysis.xai.important_features?.length > 0 && (
                          <div className="ai-summary-features">
                            <strong>{t('xai.importantFeatures')}:</strong>
                            {analysis.xai.important_features.slice(0, 4).map((feat, i) => (
                              <span key={i} className="ai-feature-tag">{feat.display_name}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p style={{ color: 'var(--text-secondary)' }}>{t('explainability.noData')}</p>
                    )}
                  </div>
                </div>

                <div className="reports-header">
                  <div className="reports-header-inner">
                    <label htmlFor="language-select">{t('reports.language')}</label>
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
                      <h3>{t('reports.healthReport')}</h3>
                      <p>{t('reports.healthReportDesc')}</p>
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
                      <h3>{t('reports.predictionsReport')}</h3>
                      <p>{t('reports.predictionsReportDesc')}</p>
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
                      <h3>{t('reports.recipesReport')}</h3>
                      <p>{t('reports.recipesReportDesc')}</p>
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
                      <h3>{t('reports.exerciseReport')}</h3>
                      <p>{t('reports.exerciseReportDesc')}</p>
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
                <p>{t('reports.noAnalysis')}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="tab-content">
            {loading ? (
              <div className="empty-state">
                <div className="empty-state-icon small">⏳</div>
                <h3>{t('predictions.loading')}</h3>
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
                        <h3>{t('predictions.mlPrediction')}</h3>
                      </div>
                      <div className="ml-prediction-body">
                        <div className="ml-prediction-main">
                          <div className="ml-predicted-class">
                            <span className="ml-label">{t('predictions.predictedClass')}</span>
                            <span className="ml-value">{analysis.ml_prediction.predicted_class.replace(/_/g, ' ')}</span>
                          </div>
                          <div className="ml-confidence">
                            <span className="ml-label">{t('predictions.confidence')}</span>
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
                      <div className="xai-card xai-card-explanation">
                        <div className="xai-card-header">
                          <span className="xai-card-icon">💡</span>
                          <h3>{t('xai.title')}</h3>
                        </div>
                        <div className="xai-card-body">
                          <p className="xai-summary">{analysis.xai.summary}</p>
                          <p className="xai-main-reason">{analysis.xai.main_reason}</p>
                        </div>
                      </div>

                      <div className="xai-card xai-card-confidence">
                        <div className="xai-card-header">
                          <span className="xai-card-icon">🎯</span>
                          <h3>{t('xai.confidenceLevel')}</h3>
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

                      {analysis.xai.important_features?.length > 0 && (
                        <div className="xai-card xai-card-features">
                          <div className="xai-card-header">
                            <span className="xai-card-icon">📊</span>
                            <h3>{t('xai.importantFeatures')}</h3>
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
                                  {feat.level === 'high' ? t('xai.high') : feat.level === 'medium' ? t('xai.medium') : t('xai.low')}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="xai-card xai-card-clinical">
                        <div className="xai-card-header">
                          <span className="xai-card-icon">🩺</span>
                          <h3>{t('xai.clinicalInterpretation')}</h3>
                        </div>
                        <div className="xai-card-body">
                          <p>{analysis.xai.risk_explanation}</p>
                          {analysis.xai.recommendations?.length > 0 && (
                            <div className="xai-recommendations">
                              <strong>{t('xai.recommendations')}</strong>
                              <ul>
                                {analysis.xai.recommendations.map((rec, i) => (
                                  <li key={i}>{rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>

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
                                  <span className="xai-scenario-label">{t('xai.projectedWeight')}</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_follow.projected_weight_kg} kg</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">{t('xai.projectedBMI')}</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_follow.projected_bmi}</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">{t('xai.expectedCategory')}</span>
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
                                  <span className="xai-scenario-label">{t('xai.estimatedWeight')}</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_ignore.projected_weight_kg} kg</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">{t('xai.estimatedBMI')}</span>
                                  <span className="xai-scenario-value">{analysis.xai.scenario_ignore.projected_bmi}</span>
                                </div>
                                <div className="xai-scenario-metric">
                                  <span className="xai-scenario-label">{t('xai.estimatedCategory')}</span>
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
                    <h3>{t('predictions.latestPrediction')}</h3>
                    <div className="metrics-grid">
                      <div className="metric-card" title="Tu peso actual al momento del análisis">
                        <div className="metric-icon">📈</div>
                        <div className="metric-label">{t('predictions.initialWeight')}</div>
                        <div className="metric-value">{Math.round(predData.profile_snapshot?.weight * 10) / 10} kg</div>
                      </div>
                      <div className="metric-card" title="Peso proyectado a 2 semanas según el modelo predictivo">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">{t('predictions.twoWeeks')}</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['2_weeks']?.weight_kg} kg
                        </div>
                      </div>
                      <div className="metric-card" title="Peso proyectado a 1 mes según el modelo predictivo">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">{t('predictions.oneMonth')}</div>
                        <div className="metric-value">
                          {predData.predictions_data?.predictions?.['1_month']?.weight_kg} kg
                        </div>
                      </div>
                      <div className="metric-card" title="Peso proyectado a 6 meses según el modelo predictivo">
                        <div className="metric-icon">🔮</div>
                        <div className="metric-label">{t('predictions.sixMonths')}</div>
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
                            name: t('predictions.prediction'),
                            x: [t('predictions.actual'), t('predictions.twoWeeks'), t('predictions.oneMonth'), t('predictions.sixMonths')],
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
                        layout={getChartLayout(t('predictions.projectionChart'), true)}
                        style={{ width: '100%' }}
                      />
                    </div>
                  </div>

                  {timelineData?.has_predictions && (
                    <div className="prediction-card">
                      <h3>{t('predictions.actualVsPredicted')}</h3>
                      {timelineData.actual_progress && timelineData.actual_progress.length > 0 ? (
                        <Plot
                          data={[
                            {
                              type: 'scatter',
                              mode: 'lines+markers',
                              name: t('predictions.prediction'),
                              x: [t('predictions.start'), t('predictions.twoWeeks'), t('predictions.oneMonth'), t('predictions.sixMonths')],
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
                              name: t('predictions.realProgress'),
                              x: timelineData.actual_progress.map(p => new Date(p.date).toLocaleDateString()),
                              y: timelineData.actual_progress.map(p => p.weight_kg),
                              marker: { color: '#10b981', size: 10 },
                              line: { color: '#10b981', width: 2 }
                            }
                          ]}
                          layout={getChartLayout(t('predictions.comparisonChart'), true)}
                          style={{ width: '100%' }}
                        />
                      ) : (
                        <div className="empty-state prediction-empty">
                          <p>{t('predictions.noProgress')}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {statsData?.has_stats && (
                    <div className="grid-2">
                      <div className="card">
                        <h3>{t('predictions.accuracyStats')}</h3>
                        <div className="prediction-stat-center">
                          <div className="prediction-accuracy-value">
                            {statsData.average_accuracy}%
                          </div>
                          <div className="prediction-accuracy-label">{t('predictions.avgAccuracy')}</div>
                        </div>
                      </div>
                      <div className="card">
                        <h3>{t('predictions.predictionHistory')}</h3>
                        {statsData.details?.map((stat, i) => (
                          <div key={i} className="goal-item">
                            <div>
                              <div className="prediction-stat-value">
                                {new Date(stat.date).toLocaleDateString()}
                              </div>
                              {stat.accuracy?.['2_weeks'] && (
                                <div className="prediction-stat-detail">
                                  {t('predictions.twoWeeks')}: {stat.accuracy['2_weeks'].accuracy_pct}%
                                </div>
                              )}
                              {stat.accuracy?.['1_month'] && (
                                <div className="prediction-stat-detail">
                                  {t('predictions.oneMonth')}: {stat.accuracy['1_month'].accuracy_pct}%
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
                  <h3>{t('predictions.emptyTitle')}</h3>
                  <p>{t('predictions.emptyDesc')}</p>
                </div>
              );
            })()}

          </div>
        )}

        {activeTab === 'explainability' && (
          <div className="tab-content">
            <ExplainabilityCenter
              analysis={analysis}
              latestPrediction={analysis?.ml_prediction || latestPrediction}
              importanceData={importanceData}
            />
          </div>
        )}
      </main>

      <HealthAssistant
        analysis={analysis}
        latestPrediction={analysis?.ml_prediction || latestPrediction}
        xaiData={analysis?.xai || null}
      />
    </div>
  );
}

export default Dashboard;
