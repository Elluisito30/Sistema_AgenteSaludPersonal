import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';

const shell = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '60vh',
  gap: 16,
  width: '100%',
  textAlign: 'center',
};

const btnPrimary = {
  padding: '14px 32px',
  borderRadius: 14,
  border: 'none',
  background: 'var(--primary)',
  color: '#fff',
  fontSize: 15,
  fontWeight: 700,
  cursor: 'pointer',
};

const btnSecondary = {
  padding: '10px 20px',
  borderRadius: 12,
  border: '1px solid var(--border)',
  background: 'var(--surface)',
  color: 'var(--text)',
  fontSize: 13,
  fontWeight: 600,
  cursor: 'pointer',
};

function JourneyPage() {
  const { t } = useTranslation();
  const { token } = useAuth();
  const { apiRequest } = useApi();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const journeyRes = await apiRequest('/api/journey/summary', 'GET', null, token);
      if (journeyRes.success) setSummary(journeyRes.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="journey-gate" style={{ ...shell, gap: 8 }}>
        <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>{t('common.loading')}</div>
      </div>
    );
  }

  // 1) Sin perfil → bienvenida + iniciar pasarela
  if (!summary?.has_profile) {
    return (
      <div className="journey-gate" style={shell}>
        <div style={{ fontSize: 48 }}>👋</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', margin: 0 }}>
          {t('onboarding.welcomeTitle')}
        </h2>
        <p style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 400, margin: 0, lineHeight: 1.5 }}>
          {t('onboarding.welcomeDesc')}
        </p>
        <button onClick={() => navigate('/onboarding')} style={btnPrimary}>
          {t('onboarding.startBtn')}
        </button>
      </div>
    );
  }

  // 2) Con perfil, sin análisis → ir a Dashboard a analizar + opción de repetir pasarela
  if (!summary?.has_analysis) {
    return (
      <div className="journey-gate" style={shell}>
        <div style={{ fontSize: 48 }}>✅</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', margin: 0 }}>
          {t('journey.profileReadyTitle')}
        </h2>
        <p style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 420, margin: 0, lineHeight: 1.5 }}>
          {t('journey.profileReadyDesc')}
        </p>
        <button onClick={() => navigate('/dashboard')} style={btnPrimary}>
          {t('journey.goToAnalyze')}
        </button>
        <button onClick={() => navigate('/onboarding')} style={btnSecondary}>
          {t('journey.repeatOnboarding')}
        </button>
      </div>
    );
  }

  // 3) Ya hay análisis → solo ir al Dashboard (sin repetir pasarela)
  return (
    <div className="journey-gate" style={shell}>
      <div style={{ fontSize: 48 }}>🎯</div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', margin: 0 }}>
        {t('journey.analysisReadyTitle')}
      </h2>
      <p style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 420, margin: 0, lineHeight: 1.5 }}>
        {t('journey.analysisReadyDesc')}
      </p>
      <button onClick={() => navigate('/dashboard')} style={btnPrimary}>
        {t('journey.goToDashboard')}
      </button>
    </div>
  );
}

export default JourneyPage;
