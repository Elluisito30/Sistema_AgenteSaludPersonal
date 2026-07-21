import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import AuthPage from './pages/AuthPage';
import AppLayout from './components/layout/AppLayout';
import OnboardingPage from './pages/OnboardingPage';
import JourneyPage from './pages/JourneyPage';
import Dashboard from './pages/Dashboard';
import DiaryPage from './pages/DiaryPage';
import FoodPage from './pages/FoodPage';
import ProfilePage from './pages/ProfilePage';
import ModelsValidationPage from './pages/ModelsValidationPage';
import ModelTrainingPage from './pages/ModelTrainingPage';
import './i18n';

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/auth" replace />;
  return children;
}

function PublicRoute({ children }) {
  const { token } = useAuth();
  if (token) return <Navigate to="/journey" replace />;
  return children;
}

function AppRoutes() {
  const { token } = useAuth();

  return (
    <Routes>
      <Route
        path="/auth"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/journey" replace />} />
        <Route path="onboarding" element={<OnboardingPage />} />
        <Route path="journey" element={<JourneyPage />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="diary" element={<DiaryPage />} />
        <Route path="food" element={<FoodPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="models" element={<ModelsValidationPage />} />
        <Route path="training" element={<ModelTrainingPage />} />
      </Route>
      <Route path="*" element={<Navigate to={token ? '/journey' : '/auth'} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
