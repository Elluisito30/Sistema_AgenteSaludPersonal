import React, { createContext, useContext, useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(sessionStorage.getItem('token') || null);
  const [user, setUser] = useState(JSON.parse(sessionStorage.getItem('user')) || null);
  const { apiRequest } = useApi();

  useEffect(() => {
    if (token) {
      sessionStorage.setItem('token', token);
    } else {
      sessionStorage.removeItem('token');
    }
    if (user) {
      sessionStorage.setItem('user', JSON.stringify(user));
    } else {
      sessionStorage.removeItem('user');
    }
  }, [token, user]);

  const login = async (email, password) => {
    const result = await apiRequest('/api/login', 'POST', { email, password });
    if (result.success) {
      setToken(result.data.access_token);
      setUser({
        user_id: result.data.user_id,
        full_name: result.data.full_name,
        email: result.data.email
      });
    }
    return result;
  };

  const register = async (fullName, email, password, phone) => {
    const result = await apiRequest('/api/register', 'POST', {
      full_name: fullName,
      email,
      password,
      phone_number: phone || null
    });
    if (result.success) {
      setToken(result.data.access_token);
      setUser({
        user_id: result.data.user_id,
        full_name: fullName,
        email
      });
    }
    return result;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      token,
      user,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
