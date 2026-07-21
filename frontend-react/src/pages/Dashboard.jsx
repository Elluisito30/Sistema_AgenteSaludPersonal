import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { useTranslation } from 'react-i18next';
import Plot from 'react-plotly.js';
import ExplainabilityCenter from '../components/ExplainabilityCenter';
import { useAnalysis } from '../components/layout/AppLayout';
import './Dashboard.css';

const GOAL_KEYS = {
  weight_loss: 'goals.weightLoss',
  muscle_gain: 'goals.muscleGain',
  better_sleep: 'goals.betterSleep',
  stress_reduction: 'goals.stressReduction',
  energy_boost: 'goals.energyBoost',
  general_wellness: 'goals.generalWellness',
};

const ACTIVITY_KEYS = {
  sedentary: 'profile.sedentary',
  light: 'profile.light',
  moderate: 'profile.moderate',
  active: 'profile.active',
  very_active: 'profile.veryActive',
  veryActive: 'profile.veryActive',
};

function Dashboard() {
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const {
    setAnalysis: setSharedAnalysis,
    setLatestPrediction: setSharedPrediction,
    setXaiData: setSharedXai,
  } = useAnalysis();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [profile, setProfile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [timelineData, setTimelineData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [importanceData, setImportanceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [message, setMessage] = useState(null);
  const [reportLanguage, setReportLanguage] = useState('es');
  const [diarySummary, setDiarySummary] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [modelType, setModelType] = useState(null);

  useEffect(() => {
    loadInitialData();
    loadModelType();
  }, []);

  const loadModelType = async () => {
    try {
      const res = await apiRequest('/api/training/model-type', 'GET', null, token);
      if (res.success) {
        setModelType(res.data);
      }
    } catch (e) {
      console.error('Error loading model type:', e);
    }
  };

  useEffect(() => {
    if (activeTab === 'explainability') {
      loadPredictions();
    }
  }, [activeTab]);

  const loadLatestAnalysis = async () => {
    const histRes = await apiRequest('/api/history?limit=1', 'GET', null, token);
    if (!histRes.success || !histRes.data?.length) return null;
    const detailRes = await apiRequest(`/api/analysis/${histRes.data[0].id}`, 'GET', null, token);
    if (detailRes.success) return detailRes.data;
    return null;
  };

  const loadInitialData = async () => {
    setInitialLoading(true);
    try {
      const profileRes = await apiRequest('/api/profile', 'GET', null, token);
      if (profileRes.success) {
        setProfile(profileRes.data);
      }

      const latestAnalysis = await loadLatestAnalysis();
      if (latestAnalysis) {
        setAnalysis(latestAnalysis);
        setSharedAnalysis(latestAnalysis);
        if (latestAnalysis.xai) {
          setSharedXai(latestAnalysis.xai);
        }
      }
    } catch (e) {
      console.error('Error loading dashboard data:', e);
    }
    setInitialLoading(false);
  };

  const loadPredictions = async () => {
    try {
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

      try {
        const diaryRes = await apiRequest('/api/diary/summary', 'GET', null, token);
        if (diaryRes.success) setDiarySummary(diaryRes.data);
      } catch (e) { /* diary optional */ }
    } catch (e) {
      console.error('Error loading predictions:', e);
    }
  };

  const analyzeHealth = async () => {
    if (!profile) {
      setMessage({ type: 'error', text: t('dashboard.noProfile') });
      return;
    }
    setLoading(true);
    setMessage({ type: 'info', text: t('messages.analyzing') });

    const result = await apiRequest('/api/analyze', 'POST', null, token);

    if (result.success) {
      setAnalysis(result.data);
      setSharedAnalysis(result.data);
      if (result.data?.ml_prediction) {
        setLatestPrediction(result.data.ml_prediction);
        setSharedPrediction(result.data.ml_prediction);
      }
      if (result.data?.xai) {
        setSharedXai(result.data.xai);
      }
      setMessage({ type: 'success', text: t('messages.analysisComplete') });
      await loadPredictions();
    } else {
      setMessage({ type: 'error', text: result.error });
    }
    setLoading(false);
    setTimeout(() => setMessage(null), 3000);
  };

  const confirmDeleteAnalysis = async () => {
    setShowDeleteConfirm(false);
    setLoading(true);
    setMessage({ type: 'info', text: 'Eliminando análisis...' });

    const result = await apiRequest('/api/analysis', 'DELETE', null, token);

    if (result.success) {
      setAnalysis(null);
      setSharedAnalysis(null);
      setSharedXai(null);
      setMessage({ type: 'success', text: 'Análisis eliminado correctamente.' });
    } else {
      setMessage({ type: 'error', text: result.error || 'Error al eliminar' });
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
    <div>
      <div className="dashboard-tabs">
        {[
          ['dashboard', '📊', t('nav.dashboard')],
          ['nutrition', '🥗', t('nav.nutrition')],
          ['exercise', '💪', t('nav.exercise')],
          ['explainability', '🔍', t('nav.explainability')],
          ['reports', '📑', t('nav.reports')],
        ].map(([key, icon, label]) => (
          <button
            key={key}
            className={`dashboard-tab ${activeTab === key ? 'active' : ''}`}
            onClick={() => setActiveTab(key)}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      <main className="main-content-dashboard">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div>
            <h1 className="page-title">{t('app.subtitle')}</h1>
            <p className="page-subtitle">{t('app.description')}</p>
          </div>
          {modelType && (
            <div style={{
              padding: '6px 12px',
              borderRadius: '12px',
              background: modelType.model_type === 'custom' ? '#d4edda' : '#e2e3e5',
              color: modelType.model_type === 'custom' ? '#155724' : '#383d41',
              fontSize: '0.75rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <span>{modelType.model_type === 'custom' ? '✅' : 'ℹ️'}</span>
              <span>Modelos: {modelType.model_type === 'custom' ? 'Personalizados' : 'Pre-entrenados'}</span>
            </div>
          )}
        </div>

        {message && (
          <div className={`message ${message.type}`}>
            <span className="message-icon">
              {message.type === 'success' ? '✓' : message.type === 'error' ? '✕' : 'ℹ'}
            </span>
            {message.text}
          </div>
        )}

        {initialLoading ? (
          <div className="empty-state">
            <p>{t('common.loading')}</p>
          </div>
        ) : null}

        {!initialLoading && (
          <div className="tab-content">
            <div className="analysis-grid">
              <div>
                <div className="profile-section">
                  <h3>📝 {t('profile.title')}</h3>
                  <p className="profile-readonly-hint">{t('dashboard.profileReadonlyHint')}</p>

                  {!profile ? (
                    <div className="empty-state" style={{ padding: '24px 16px' }}>
                      <p>{t('dashboard.noProfile')}</p>
                      <button type="button" className="btn-primary" onClick={() => navigate('/onboarding')}>
                        {t('onboarding.startBtn')}
                      </button>
                    </div>
                  ) : (
                    <div className="profile-readonly">
                      <div className="profile-readonly-section">{t('profile.personalData')}</div>
                      <div className="profile-readonly-grid">
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.age')}</span>
                          <span className="profile-readonly-value">{profile.age ?? '—'}</span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.gender')}</span>
                          <span className="profile-readonly-value">
                            {profile.gender === 'female' ? t('profile.female') : profile.gender === 'male' ? t('profile.male') : '—'}
                          </span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.weight')}</span>
                          <span className="profile-readonly-value">{profile.weight_kg != null ? `${profile.weight_kg} kg` : '—'}</span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.height')}</span>
                          <span className="profile-readonly-value">{profile.height_cm != null ? `${profile.height_cm} cm` : '—'}</span>
                        </div>
                      </div>

                      <div className="profile-readonly-section">{t('profile.lifestyle')}</div>
                      <div className="profile-readonly-grid">
                        <div className="profile-readonly-item full-width">
                          <span className="profile-readonly-label">{t('profile.activityLevel')}</span>
                          <span className="profile-readonly-value">
                            {t(ACTIVITY_KEYS[profile.activity_level] || 'profile.moderate')}
                          </span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.sleepHours')}</span>
                          <span className="profile-readonly-value">{profile.sleep_hours ?? 7}h</span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.geneticRisk')}</span>
                          <span className="profile-readonly-value">
                            {profile.genetics_risk === 'high'
                              ? t('profile.geneticHigh')
                              : profile.genetics_risk === 'medium'
                                ? t('profile.geneticMedium')
                                : t('profile.geneticLow')}
                          </span>
                        </div>
                      </div>

                      <div className="profile-readonly-section">{t('profile.health')}</div>
                      <div className="profile-readonly-grid">
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.smoker')}</span>
                          <span className="profile-readonly-value">{profile.smokes ? t('onboarding.yes') : t('onboarding.no')}</span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('profile.familyHistory')}</span>
                          <span className="profile-readonly-value">{profile.family_history ? t('onboarding.yes') : t('onboarding.no')}</span>
                        </div>
                        <div className="profile-readonly-item full-width">
                          <span className="profile-readonly-label">{t('profile.chronicConditions')}</span>
                          <span className="profile-readonly-value">
                            {profile.has_chronic_conditions
                              ? (profile.chronic_conditions_detail || t('onboarding.yes'))
                              : t('onboarding.no')}
                          </span>
                        </div>
                      </div>

                      <div className="profile-readonly-section">{t('profile.nutritionSection')}</div>
                      <div className="profile-readonly-grid">
                        <div className="profile-readonly-item full-width">
                          <span className="profile-readonly-label">{t('profile.fastFood')}</span>
                          <span className="profile-readonly-value">
                            {profile.favc === 'Always' ? t('profile.fastFoodAlways')
                              : profile.favc === 'Frequently' ? t('profile.fastFoodFrequently')
                              : profile.favc === 'No' ? t('profile.fastFoodNo')
                              : t('profile.fastFoodSometimes')}
                          </span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('onboarding.vegetables')}</span>
                          <span className="profile-readonly-value">
                            {Number(profile.fcvc) === 1 ? t('profile.veg1')
                              : Number(profile.fcvc) === 3 ? t('profile.veg3')
                              : t('profile.veg2')}
                          </span>
                        </div>
                        <div className="profile-readonly-item">
                          <span className="profile-readonly-label">{t('onboarding.water')}</span>
                          <span className="profile-readonly-value">
                            {Number(profile.ch2o) === 1 ? t('profile.water1')
                              : Number(profile.ch2o) === 3 ? t('profile.water3')
                              : t('profile.water2')}
                          </span>
                        </div>
                      </div>

                      <div className="profile-readonly-section">{t('profile.goalsSection')}</div>
                      <div className="profile-readonly-grid">
                        <div className="profile-readonly-item full-width">
                          <span className="profile-readonly-label">{t('profile.healthGoals')}</span>
                          <span className="profile-readonly-value">
                            {(profile.health_goals || []).length
                              ? profile.health_goals.map(g => t(GOAL_KEYS[g] || g)).join(', ')
                              : t('dashboard.noGoals')}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="analyze-button-area">
                  <button
                    type="button"
                    onClick={analyzeHealth}
                    className={`btn-primary btn-large ${loading ? 'loading' : ''}`}
                    disabled={loading || !profile}
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
                  {analysis && (
                    <>
                      <button
                        type="button"
                        className="btn-danger"
                        style={{ marginTop: 10, width: '100%', background: 'var(--danger)', color: 'white', border: 'none', padding: '12px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
                        onClick={() => setShowDeleteConfirm(true)}
                        disabled={loading}
                      >
                        🗑️ Eliminar Análisis
                      </button>

                      {showDeleteConfirm && (
                        <div style={{ marginTop: '10px', padding: '15px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid var(--danger)' }}>
                          <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: 'var(--danger)', fontWeight: 600, lineHeight: 1.4 }}>¿Estás seguro de eliminar permanentemente todos tus análisis y proyecciones? Tendrás que generar uno nuevo.</p>
                          <div style={{ display: 'flex', gap: '10px' }}>
                            <button 
                              type="button" 
                              onClick={confirmDeleteAnalysis}
                              style={{ flex: 1, padding: '8px', background: 'var(--danger)', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
                            >
                              Sí, eliminar
                            </button>
                            <button 
                              type="button" 
                              onClick={() => setShowDeleteConfirm(false)}
                              style={{ flex: 1, padding: '8px', background: 'var(--border)', color: 'var(--text-color, #333)', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
                            >
                              Cancelar
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                  {profile && (
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ marginTop: 10, width: '100%' }}
                      onClick={() => navigate('/profile')}
                    >
                      {t('dashboard.editProfile')}
                    </button>
                  )}
                </div>
              </div>

              <div className="analysis-results">
                {activeTab === 'dashboard' && (
                  <>
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
                        <div className="analysis-card-value tooltip-trigger" title={`IMC: ${analysis.bmi} — Categoría: ${t(`analysis.bmiCategory.${analysis.bmi_category}`) || String(analysis.bmi_category || '').replace('_', ' ')}. Valores normales: 18.5 – 24.9`}>{analysis.bmi}</div>
                        <div className="analysis-card-desc">{t('analysis.bmiDesc')}</div>
                        <span className={`analysis-card-badge ${analysis.bmi_category === 'normal' ? '' : (analysis.bmi_category?.startsWith('obese') ? 'danger' : 'warning')}`}>
                          {t(`analysis.bmiCategory.${analysis.bmi_category}`) || String(analysis.bmi_category || '').replace('_', ' ')}
                        </span>
                      </div>

                      <div className="analysis-card calories">
                        <div className="analysis-card-icon" title="Total de Energía Diaria Expendida — calorías que tu cuerpo necesita al día">🔥</div>
                        <div className="analysis-card-label">{t('analysis.dailyCalories')}</div>
                        <div className="analysis-card-value tooltip-trigger" title={`TDEE: ${Number(analysis.tdee || 0).toFixed(0)} kcal/día. Calculado según tu nivel de actividad, peso, altura y objetivo.`}>{Number(analysis.tdee || 0).toFixed(0)}</div>
                        <div className="analysis-card-desc">{t('analysis.caloriesDesc')}</div>
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
                                {alert.priority === 'high' || (alert.message || '').includes('Clínica') ? '🚨' : '⚠️'} {alert.message || alert}
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
                            analysis.weekly_goals.map((goal, i) => {
                              // Handle both old string goals and new key/params goals
                              let goalText;
                              if (typeof goal === 'object' && goal?.key) {
                                goalText = t(`weeklyGoals.${goal.key}`, goal.params || {});
                              } else if (typeof goal === 'string' && goal.startsWith('weeklyGoals.')) {
                                // Handle backend returning literal translation keys
                                goalText = t(goal);
                              } else {
                                goalText = goal;
                              }
                              return <p key={i}>🎯 {goalText}</p>;
                            })
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
                  </>
                )}

                {activeTab === 'nutrition' && (
                  <div className="tab-content-inner">
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
                  <div className="tab-content-inner">
            {analysis?.health_plan?.exercise ? (
              <div>
                <div className="exercise-kpi-grid">
                  <div className="exercise-kpi-card">
                    <div className="exercise-kpi-icon">
                      {analysis.fitness_level === 'beginner' ? '🌱' :
                        analysis.fitness_level === 'advanced' ? '🏆' : '💪'}
                    </div>
                    <div className="exercise-kpi-label">{t('exercise.yourLevel')}</div>
                    <div className="exercise-kpi-value">{analysis.fitness_level}</div>
                  </div>

                  <div className="exercise-kpi-card">
                    <div className="exercise-kpi-icon">🏃</div>
                    <div className="exercise-kpi-label">{t('exercise.cardio')}</div>
                    <div className="exercise-kpi-value">{analysis.health_plan.exercise.cardio}</div>
                  </div>

                  <div className="exercise-kpi-card">
                    <div className="exercise-kpi-icon">🏋️</div>
                    <div className="exercise-kpi-label">{t('exercise.strength')}</div>
                    <div className="exercise-kpi-value">{analysis.health_plan.exercise.strength}</div>
                  </div>

                  <div className="exercise-kpi-card">
                    <div className="exercise-kpi-icon">🧘</div>
                    <div className="exercise-kpi-label">{t('exercise.flexibility')}</div>
                    <div className="exercise-kpi-value">{analysis.health_plan.exercise.flexibility}</div>
                  </div>
                </div>

                <div className="card">
                  <h3>{t('exercise.weeklyPlan')}</h3>
                  <p className="card-subtitle">{t('exercise.weeklyRoutine')}</p>
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
                  <div className="tab-content-inner">
            {analysis ? (
              <div>
                <div className="reports-summaries">
                  <div className="report-summary-card executive-kpi-panel">
                    <h3>📋 {t('reports.executiveSummary')}</h3>
                    <div className="kpi-panel-grid">
                      <div className="kpi-panel-item">
                        <div className="kpi-panel-icon">❤️</div>
                        <div className="kpi-panel-label">{t('analysis.healthScore')}</div>
                        <div className="kpi-panel-value" style={{ color: getScoreColorVar(analysis.health_score) }}>{analysis.health_score}</div>
                        <div className="kpi-panel-suffix">/100</div>
                      </div>
                      <div className="kpi-panel-item">
                        <div className="kpi-panel-icon">⚖️</div>
                        <div className="kpi-panel-label">{t('analysis.bmi')}</div>
                        <div className="kpi-panel-value">{analysis.bmi}</div>
                      </div>
                      <div className="kpi-panel-item">
                        <div className="kpi-panel-icon">🔥</div>
                        <div className="kpi-panel-label">{t('analysis.tdee')}</div>
                        <div className="kpi-panel-value">{analysis.tdee?.toFixed(0)}</div>
                        <div className="kpi-panel-suffix">kcal</div>
                      </div>
                    </div>
                    {analysis.alerts?.length > 0 && (
                      <div className="kpi-panel-section">
                        <div className="kpi-panel-section-title">
                          {analysis.alerts.some(a => a.severity === 'high' || a.severity === 'critical') ? '⚠️' : 'ℹ️'} {t('reports.riskFactors')}
                        </div>
                        <div className="kpi-panel-list">
                          {analysis.alerts.slice(0, 3).map((alert, i) => (
                            <div key={i} className="kpi-panel-list-item">{alert.message || alert}</div>
                          ))}
                        </div>
                      </div>
                    )}
                    {analysis.weekly_goals?.length > 0 && (
                      <div className="kpi-panel-section">
                        <div className="kpi-panel-section-title">🎯 {t('reports.improvements')}</div>
                        <div className="kpi-panel-list">
                          {analysis.weekly_goals.slice(0, 3).map((goal, i) => {
                            let goalText;
                            if (typeof goal === 'object' && goal?.key) {
                              goalText = t(`weeklyGoals.${goal.key}`, goal.params || {});
                            } else if (typeof goal === 'string' && goal.startsWith('weeklyGoals.')) {
                              // Handle backend returning literal translation keys
                              goalText = t(goal);
                            } else {
                              goalText = goal;
                            }
                            return <div key={i} className="kpi-panel-list-item">{goalText}</div>;
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="report-summary-card clinical-summary-card">
                    <h3>⚕️ {t('reports.clinicalSummary')}</h3>
                    <div className="clinical-metrics-grid">
                      <div className="clinical-metric-item">
                        <div className="clinical-metric-label">{t('analysis.bmi')}</div>
                        <div className="clinical-metric-value">{analysis.bmi}</div>
                        <div className="clinical-metric-sub">{analysis.bmi_category?.replace('_', ' ')}</div>
                      </div>
                      <div className="clinical-metric-item">
                        <div className="clinical-metric-label">{t('analysis.dailyCalories')}</div>
                        <div className="clinical-metric-value">{analysis.health_plan?.nutrition?.daily_calories || 'N/A'}</div>
                        <div className="clinical-metric-sub">kcal/día</div>
                      </div>
                    </div>
                    {analysis.health_plan?.nutrition?.recommendations?.length > 0 && (
                      <div className="clinical-recommendations">
                        <div className="clinical-section-title">💡 {t('reports.improvements')}</div>
                        <div className="clinical-recommendations-list">
                          {analysis.health_plan.nutrition.recommendations.slice(0, 3).map((rec, i) => (
                            <div key={i} className="clinical-recommendation-item">✓ {rec}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="report-summary-card ai-summary-card">
                    <h3>🤖 {t('reports.aiSummary')}</h3>
                    {analysis.xai ? (
                      <div className="ai-summary-content">
                        <div className="ai-explanation-box">
                          <div className="ai-explanation-icon">💡</div>
                          <div className="ai-explanation-text">
                            <p className="ai-explanation-main">{analysis.xai.risk_explanation}</p>
                          </div>
                        </div>
                        {analysis.ml_prediction && (
                          <div className="ai-model-info">
                            <span className="ai-model-badge">{analysis.ml_prediction.model_used}</span>
                            <span className="ai-confidence-badge">Confianza: {analysis.ml_prediction.confidence?.toFixed(1)}%</span>
                          </div>
                        )}
                        {analysis.xai.important_features?.length > 0 && (
                          <div className="ai-factors-section">
                            <div className="ai-factors-title">🔍 Factores más influyentes</div>
                            <div className="ai-factors-list">
                              {analysis.xai.important_features.slice(0, 4).map((feat, i) => (
                                <div key={i} className="ai-factor-item">
                                  <span className="ai-factor-name">{feat.display_name}</span>
                                  <span className="ai-factor-impact">{feat.impact > 0 ? '↑' : '↓'}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p style={{ color: 'var(--text-secondary)' }}>{t('explainability.noData')}</p>
                    )}
                  </div>

                  <div className="report-summary-card report-summary-ml-compare">
                    <h3>📊 {t('enhanced.mlModelComparison')}</h3>
                    <div className="ml-compare-grid">
                      <div className="ml-model-card">
                        <div className="ml-model-header">
                          <span className="ml-model-name">XGBoost</span>
                          <span className="ml-model-tag ml-model-primary">{t('enhanced.productionModel')}</span>
                        </div>
                        <div className="ml-model-accuracy">
                          <span className="ml-accuracy-value">99.05%</span>
                          <span className="ml-accuracy-label">{t('enhanced.accuracy')}</span>
                        </div>
                        <div className="ml-model-features">
                          <span>11 {t('enhanced.featuresUsed')}</span>
                          <span>117 {t('enhanced.trainingSamples')}</span>
                        </div>
                      </div>
                      <div className="ml-model-divider">vs</div>
                      <div className="ml-model-card ml-model-secondary">
                        <div className="ml-model-header">
                          <span className="ml-model-name">Neural Network</span>
                          <span className="ml-model-tag ml-model-secondary-tag">Keras/TensorFlow</span>
                        </div>
                        <div className="ml-model-accuracy">
                          <span className="ml-accuracy-value">93.69%</span>
                          <span className="ml-accuracy-label">{t('enhanced.accuracy')}</span>
                        </div>
                        <div className="ml-model-features">
                          <span>11 {t('enhanced.featuresUsed')}</span>
                          <span>2 {t('enhanced.hiddenLayers')}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="report-summary-card report-summary-diary">
                    <h3>📝 {t('enhanced.diarySummary')}</h3>
                    {diarySummary ? (
                      <div className="diary-summary-content">
                        <div className="diary-summary-stats">
                          {diarySummary.streak_days > 0 && (
                            <div className="diary-stat-badge diary-streak">
                              🔥 {diarySummary.streak_days} {t('enhanced.streakDays')}
                            </div>
                          )}
                          <div className="diary-stat-badge diary-entries">
                            📋 {diarySummary.total_entries || 0} {t('enhanced.totalEntries')}
                          </div>
                        </div>
                        {diarySummary.today && (
                          <div className="diary-today-summary">
                            <strong>{t('diary.today')}:</strong>
                            <div className="diary-today-pills">
                              {diarySummary.today.water_liters > 0 && (
                                <span className="diary-pill diary-water">💧 {diarySummary.today.water_liters}L</span>
                              )}
                              {diarySummary.today.calories_consumed > 0 && (
                                <span className="diary-pill diary-calories">🔥 {diarySummary.today.calories_consumed}kcal</span>
                              )}
                              {diarySummary.today.exercise_minutes > 0 && (
                                <span className="diary-pill diary-exercise">🏃 {diarySummary.today.exercise_minutes}min</span>
                              )}
                              {diarySummary.today.sleep_hours > 0 && (
                                <span className="diary-pill diary-sleep">😴 {diarySummary.today.sleep_hours}h</span>
                              )}
                              {diarySummary.today.mood && (
                                <span className="diary-pill diary-mood">😊 {t(`onboarding.moods.${diarySummary.today.mood}`)}</span>
                              )}
                            </div>
                          </div>
                        )}
                        {(!diarySummary.today || Object.keys(diarySummary.today).length === 0) && diarySummary.total_entries === 0 && (
                          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                            {t('diary.noEntries')} — <a href="/diary" style={{ color: 'var(--primary)' }}>{t('enhanced.startTracking')}</a>
                          </p>
                        )}
                      </div>
                    ) : (
                      <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{t('enhanced.loadingDiary')}</p>
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
                {activeTab === 'explainability' && (
                  <div className="tab-content-inner">
                    <ExplainabilityCenter
                      analysis={analysis}
                      latestPrediction={analysis?.ml_prediction || latestPrediction}
                      importanceData={importanceData}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
