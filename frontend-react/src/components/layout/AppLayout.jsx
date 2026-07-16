import React, { useState, useEffect, createContext, useContext } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '../LanguageSwitcher';
import ThemeToggle from '../ThemeToggle';
import HealthAssistant from '../HealthAssistant';
import { useApi } from '../../hooks/useApi';
import './AppLayout.css';

const AnalysisContext = createContext();
export const useAnalysis = () => useContext(AnalysisContext);

function AppLayout() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const { apiRequest } = useApi();
  const location = useLocation();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [latestPrediction, setLatestPrediction] = useState(null);
  const [xaiData, setXaiData] = useState(null);

  const loadAnalysis = async () => {
    try {
      const histRes = await apiRequest('/api/history?limit=1', 'GET', null, null);
      if (!histRes.success || !histRes.data?.length) return;
      const id = histRes.data[0].id;
      const detailRes = await apiRequest(`/api/analysis/${id}`, 'GET', null, null);
      if (detailRes.success) {
        setAnalysis(detailRes.data);
        setLatestPrediction(detailRes.data?.ml_prediction || null);
        setXaiData(detailRes.data?.xai || null);
      }
    } catch (e) {
      console.error('Error loading analysis:', e);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  const isOnboarding = location.pathname === '/onboarding';

  if (isOnboarding) {
    return (
      <div className="app-layout onboarding-layout">
        <Outlet />
      </div>
    );
  }

  return (
    <AnalysisContext.Provider value={{ analysis, latestPrediction, xaiData, loadAnalysis }}>
      <div className="app-layout">
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="app-logo" onClick={() => navigate('/journey')}>
              🏥 {t('app.title')}
            </div>
            <div className="sidebar-controls">
              <LanguageSwitcher />
              <ThemeToggle />
            </div>
            <div className="user-card">
              <div className="user-avatar">
                {user?.full_name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="user-info">
                <div className="user-name">{user?.full_name || 'Usuario'}</div>
                <div className="user-email">{user?.email || ''}</div>
              </div>
            </div>
          </div>

          <nav className="nav-menu">
            <NavLink
              to="/journey"
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              🏠 {t('nav.journey')}
            </NavLink>
            <NavLink
              to="/dashboard"
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              📊 {t('nav.dashboard')}
            </NavLink>
            <NavLink
              to="/diary"
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              📓 {t('nav.diary')}
            </NavLink>
            <NavLink
              to="/food"
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              🍽️ {t('nav.food')}
            </NavLink>
            <NavLink
              to="/profile"
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              👤 {t('nav.profile')}
            </NavLink>
          </nav>

          <button className="btn-logout" onClick={logout}>
            🚪 {t('nav.logout')}
          </button>
        </aside>

        <main className="main-content">
          <Outlet />
        </main>

        <HealthAssistant
          analysis={analysis}
          latestPrediction={latestPrediction}
          xaiData={xaiData}
        />
      </div>
    </AnalysisContext.Provider>
  );
}

export default AppLayout;
