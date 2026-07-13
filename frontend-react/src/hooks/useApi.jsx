const API_BASE_URL = '';

export const useApi = () => {
  const apiRequest = async (endpoint, method = 'GET', data = null, token = null) => {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
      method,
      headers,
    };
    
    if (data) {
      config.body = JSON.stringify(data);
    }
    
    try {
      const response = await fetch(url, config);
      const result = await response.json();
      
      if (response.ok) {
        return { success: true, data: result };
      } else {
        return { success: false, error: result.detail || 'Error desconocido' };
      }
    } catch (error) {
      return { success: false, error: 'Error de conexión' };
    }
  };
  
  return { apiRequest };
};
