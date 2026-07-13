import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';

function AppContent() {
  const { token } = useAuth();
  
  return token ? <Dashboard /> : <AuthPage />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
