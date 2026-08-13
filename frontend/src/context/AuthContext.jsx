import React, { createContext, useState } from 'react';
import api from '../services/api';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('token') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  const isAuthenticated = !!token;

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const dataPayload = response.data?.data || response.data;
      const authToken = dataPayload.access_token;
      const userObj = dataPayload.user || { email, username: email.split('@')[0], role: 'ANALYST', org_id: 'org_default' };
      
      setToken(authToken);
      setUser(userObj);
      localStorage.setItem('token', authToken);
      localStorage.setItem('user', JSON.stringify(userObj));
      return { success: true };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Invalid email or password.';
      return { success: false, error: errorMsg };
    }
  };

  const register = async (username, email, password, orgName = '') => {
    try {
      await api.post('/auth/register', { username, email, password, organization_name: orgName });
      return await login(email, password);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Registration failed.';
      return { success: false, error: errorMsg };
    }
  };

  const forgotPassword = async (email) => {
    try {
      const response = await api.post('/auth/forgot-password', { email });
      return { success: true, message: response.data.message };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || err.message || 'Failed to send reset email' };
    }
  };

  const resetPassword = async (email, reset_code, new_password) => {
    try {
      const response = await api.post('/auth/reset-password', { email, reset_code, new_password });
      return { success: true, message: response.data.message };
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || err.message || 'Invalid or expired code' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, register, forgotPassword, resetPassword, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
