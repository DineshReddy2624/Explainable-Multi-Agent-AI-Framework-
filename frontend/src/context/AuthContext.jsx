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

  const loginWithOAuth = async (provider = 'google') => {
    localStorage.setItem('oauth_provider', provider);
    try {
      const response = await api.get(`/auth/oauth/authorize/${provider}`);
      const dataObj = response.data?.data || response.data;
      if (dataObj?.has_configured_client_id && dataObj?.auth_url) {
        window.location.href = dataObj.auth_url;
        return { success: true, redirecting: true };
      } else {
        return {
          success: false,
          error: "Google OAuth is not configured yet. Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend .env."
        };
      }
    } catch (err) {
      console.error("Backend OAuth authorize error:", err);
      const detail = err.response?.data?.detail || err.message || "Failed to initiate Google OAuth";
      return { success: false, error: detail };
    }
  };

  const verifyOAuthCallback = async (callbackData) => {
    try {
      const response = await api.post('/auth/oauth/verify', callbackData);
      const dataPayload = response.data?.data || response.data;
      const authToken = dataPayload.access_token;
      const rawUser = dataPayload.user || {};
      const picUrl = rawUser.picture || rawUser.avatar_url || "";

      const userObj = {
        id: rawUser.id || Date.now(),
        username: rawUser.username || (rawUser.email ? rawUser.email.split('@')[0] : 'user'),
        email: rawUser.email || `${callbackData.provider || 'google'}_user@example.com`,
        full_name: rawUser.full_name || rawUser.name || rawUser.username || (rawUser.email ? rawUser.email.split('@')[0] : 'User'),
        avatar_url: picUrl,
        picture: picUrl,
        role: rawUser.role || "ANALYST",
        org_id: rawUser.org_id || "org_default",
        google_id: rawUser.google_id || null,
        auth_provider: rawUser.auth_provider || callbackData.provider || 'google'
      };

      setToken(authToken);
      setUser(userObj);
      localStorage.setItem('token', authToken);
      localStorage.setItem('user', JSON.stringify(userObj));
      return { success: true };
    } catch (err) {
      console.error("Verify OAuth callback error:", err);
      const errDetail = err.response?.data?.detail || err.response?.data?.message || err.message || "Failed to authenticate with Google.";
      return { success: false, error: errDetail };
    }
  };




  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, register, loginWithOAuth, verifyOAuthCallback, forgotPassword, resetPassword, logout }}>
      {children}
    </AuthContext.Provider>
  );
};


