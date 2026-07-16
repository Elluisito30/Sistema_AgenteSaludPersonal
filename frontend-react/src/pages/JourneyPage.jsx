import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { useAnalysis } from '../components/layout/AppLayout';

function JourneyPage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const navigate = useNavigate();
  const { analysis, loadAnalysis } = useAnalysis();
  const [summary, setSummary] = useState(null);
  const [diarySummary, setDiarySummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [journeyRes, diaryRes] = await Promise.all([
        apiRequest('/api/journey/summary', 'GET', null, token),
        apiRequest('/api/diary/summary', 'GET', null, token)
      ]);
      if (journeyRes.success) setSummary(journeyRes.data);
      if (diaryRes.success) setDiarySummary(diaryRes.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const getGreeting = () => {
    const h = new Date().getHours();
    if (h < 12) return t('journey.goodMorning');
    if (h < 18) return t('journey.goodAfternoon');
    return t('journey.goodEvening');
  };

  const userName = JSON.parse(sessionStorage.getItem('user'))?.full_name || '';
  const score = analysis?.health_score;
  const bmi = analysis?.bmi;
  const alerts = analysis?.alerts || [];
  const streak = diarySummary?.streak_days || 0;
  const todayCalories = diarySummary?.today?.calories_consumed || 0;
  const todayWater = diarySummary?.today?.water_liters || 0;
  const todayExercise = diarySummary?.today?.exercise_minutes || 0;
  const todaySleep = diarySummary?.today?.sleep_hours || 0;

  const quickActions = [
    { icon: '🤖', label: t('journey.analyzeHealth'), action: () => navigate('/dashboard') },
    { icon: '🥣', label: t('journey.logBreakfast'), action: () => navigate('/food') },
    { icon: '🥗', label: t('journey.logLunch'), action: () => navigate('/food') },
    { icon: '📑', label: t('journey.viewReports'), action: () => navigate('/dashboard') },
  ];

  const c = (bg, border) => ({
    background: bg || 'var(--surface)', borderRadius: 16, padding: 18,
    border: `1px solid ${border || 'var(--border)'}`, transition: 'all 0.15s'
  });

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
      <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>{t('common.loading')}</div>
    </div>
  );

  if (!summary?.has_profile) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 16 }}>
      <div style={{ fontSize: 48 }}>👋</div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', margin: 0 }}>{t('onboarding.welcomeTitle')}</h2>
      <p style={{ fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', maxWidth: 400 }}>{t('onboarding.welcomeDesc')}</p>
      <button onClick={() => navigate('/onboarding')} style={{
        padding: '14px 32px', borderRadius: 14, border: 'none',
        background: 'var(--primary)', color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer'
      }}>{t('onboarding.startBtn')}</button>
    </div>
  );

  return (
    <div style={{ maxWidth: 900, animation: 'fadeIn 0.3s ease' }}>
      <h1 className="page-title" style={{ fontSize: 24, marginBottom: 2 }}>
        {getGreeting()}, {userName.split(' ')[0]} 👋
      </h1>
      <p className="page-subtitle">{t('journey.subtitle')}</p>

      {/* Health Score + BMI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 16 }}>
        {score != null && (
          <div style={c('var(--surface)')}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>❤️ {t('journey.healthScore')}</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: score >= 80 ? 'var(--secondary)' : score >= 60 ? 'var(--accent)' : 'var(--danger)' }}>
              {score}<span style={{ fontSize: 14, fontWeight: 500 }}>/100</span>
            </div>
          </div>
        )}
        {bmi != null && (
          <div style={c('var(--surface)')}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>⚖️ {t('journey.currentBMI')}</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--text)' }}>{bmi}</div>
          </div>
        )}
        <div style={c(streak > 0 ? 'rgba(16,185,129,0.04)' : 'var(--surface)')}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>🔥 {t('journey.streak')}</div>
          <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--secondary)' }}>{streak}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t('journey.streakDesc')}</div>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div style={{ ...c('rgba(239,68,68,0.04)', 'rgba(239,68,68,0.2)'), marginBottom: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--danger)', marginBottom: 6 }}>
            🚨 {t('journey.alerts')} ({alerts.length})
          </div>
          {alerts.slice(0, 2).map((a, i) => (
            <div key={i} style={{ fontSize: 12, color: 'var(--text)', padding: '4px 0' }}>
              {a.message || a}
            </div>
          ))}
        </div>
      )}

      {/* Daily Progress Cards */}
      <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', margin: '0 0 12px' }}>
        📊 {t('journey.dailyProgress')}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 20 }}>
        {[
          ['💧', t('journey.water'), `${todayWater}L`, t('journey.waterTarget')],
          ['🔥', t('journey.calories'), `${todayCalories}`, 'kcal'],
          ['👟', t('journey.steps'), `${diarySummary?.today?.steps_count || 0}`, ''],
          ['😴', t('journey.sleep'), `${todaySleep}h`, ''],
        ].map(([icon, label, value, sub]) => (
          <div key={label} style={{ ...c('var(--surface)'), textAlign: 'center', padding: 16 }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{icon}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text)' }}>{value}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', margin: '0 0 12px' }}>
        ⚡ {t('journey.quickActions')}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 20 }}>
        {quickActions.map((a, i) => (
          <button key={i} onClick={a.action} style={{
            ...c('var(--surface)'), cursor: 'pointer', textAlign: 'left',
            display: 'flex', alignItems: 'center', gap: 12, padding: 16,
            transition: 'all 0.15s', border: '1px solid var(--border)'
          }}
          onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--primary)'}
          onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <span style={{ fontSize: 24 }}>{a.icon}</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{a.label}</span>
          </button>
        ))}
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

export default JourneyPage;
