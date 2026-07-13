import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './AuthPage.css';

function AuthPage() {
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const { login, register } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    
    const email = e.target.email.value;
    const password = e.target.password.value;
    
    const result = await login(email, password);
    
    if (!result.success) {
      setMessage({ type: 'error', text: result.error });
    }
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    
    const fullName = e.target.fullName.value;
    const email = e.target.email.value;
    const phone = e.target.phone.value;
    const password = e.target.password.value;
    const password2 = e.target.password2.value;
    
    if (password !== password2) {
      setMessage({ type: 'error', text: 'Las contraseñas no coinciden' });
      setLoading(false);
      return;
    }
    
    if (password.length < 6) {
      setMessage({ type: 'error', text: 'La contraseña debe tener al menos 6 caracteres' });
      setLoading(false);
      return;
    }
    
    const result = await register(fullName, email, password, phone);
    
    if (!result.success) {
      setMessage({ type: 'error', text: result.error });
    }
    setLoading(false);
  };

  return (
    <div className="auth-container">
      {/* Fondo decorativo */}
      <div className="background-decoration"></div>
      
      <div className="auth-left">
        <div className="info-box">
          <div className="logo-container">
            <div className="logo-icon">🏥</div>
            <h1>Health AI</h1>
          </div>
          <h2>Tu Asistente Personal de Salud</h2>
          <p>Análisis inteligente, seguimiento personalizado y recomendaciones basadas en Inteligencia Artificial</p>
        </div>
        
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <div className="feature-title">Análisis de Salud</div>
            <div className="feature-desc">Insights detallados sobre tu estado físico</div>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <div className="feature-title">Predicciones IA</div>
            <div className="feature-desc">Evaluación de riesgos y metas personalizadas</div>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🥗</div>
            <div className="feature-title">Planes Personalizados</div>
            <div className="feature-desc">Nutrición y ejercicio adaptados a ti</div>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <div className="feature-title">Seguimiento</div>
            <div className="feature-desc">Monitorización de tu evolución diaria</div>
          </div>
        </div>
      </div>
      
      <div className="auth-right">
        <div className="auth-form-container">
          <div className="auth-header">
            <h3>{activeTab === 'login' ? 'Bienvenido de nuevo' : 'Crea tu cuenta'}</h3>
            <p>{activeTab === 'login' ? 'Ingresa a tu perfil de salud' : 'Comienza tu viaje hacia un bienestar mejor'}</p>
          </div>
          
          <div className="auth-tabs">
            <button 
              className={activeTab === 'login' ? 'active' : ''}
              onClick={() => {
                setActiveTab('login');
                setMessage(null);
              }}
            >
              <span className="tab-icon">🔐</span>
              Iniciar Sesión
            </button>
            <button 
              className={activeTab === 'register' ? 'active' : ''}
              onClick={() => {
                setActiveTab('register');
                setMessage(null);
              }}
            >
              <span className="tab-icon">📝</span>
              Registrarse
            </button>
          </div>

          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}

          {activeTab === 'login' ? (
            <form onSubmit={handleLogin} className="auth-form">
              <div className="form-group">
                <label>
                  <span className="label-icon">📧</span>
                  Email
                </label>
                <input type="email" name="email" required placeholder="tu@email.com" />
              </div>
              <div className="form-group">
                <label>
                  <span className="label-icon">🔒</span>
                  Contraseña
                </label>
                <input type="password" name="password" required placeholder="••••••••" />
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? (
                  <span className="loading-spinner"></span>
                ) : (
                  'Ingresar'
                )}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="auth-form">
              <div className="form-group">
                <label>
                  <span className="label-icon">👤</span>
                  Nombre Completo
                </label>
                <input type="text" name="fullName" required placeholder="Tu nombre completo" />
              </div>
              <div className="form-group">
                <label>
                  <span className="label-icon">📧</span>
                  Email
                </label>
                <input type="email" name="email" required placeholder="tu@email.com" />
              </div>
              <div className="form-group">
                <label>
                  <span className="label-icon">📱</span>
                  Teléfono (opcional)
                </label>
                <input type="text" name="phone" placeholder="+51 987 654 321" />
              </div>
              <div className="form-group">
                <label>
                  <span className="label-icon">🔒</span>
                  Contraseña
                </label>
                <input type="password" name="password" required placeholder="••••••••" />
              </div>
              <div className="form-group">
                <label>
                  <span className="label-icon">🔒</span>
                  Confirmar Contraseña
                </label>
                <input type="password" name="password2" required placeholder="••••••••" />
              </div>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? (
                  <span className="loading-spinner"></span>
                ) : (
                  'Crear Cuenta'
                )}
              </button>
            </form>
          )}
        </div>
        
        <div className="footer">
          <p className="security-text">🔒 Tus datos están seguros y protegidos</p>
          <p className="copyright">Health AI © 2025 - Tecnología de salud avanzada</p>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
