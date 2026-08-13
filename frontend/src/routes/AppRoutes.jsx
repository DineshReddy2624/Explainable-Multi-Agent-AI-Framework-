import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import UploadDataset from '../pages/UploadDataset';
import DataProfiling from '../pages/DataProfiling';
import Issues from '../pages/Issues';
import Anomalies from '../pages/Anomalies';
import Corrections from '../pages/Corrections';
import Explainability from '../pages/Explainability';
import Monitoring from '../pages/Monitoring';
import RuleEngine from '../pages/RuleEngine';
import ChatWithDataset from '../pages/ChatWithDataset';
import Reports from '../pages/Reports';
import History from '../pages/History';
import Settings from '../pages/Settings';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
      />
      <Route
        path="/dashboard"
        element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
      />
      <Route
        path="/upload"
        element={<ProtectedRoute><UploadDataset /></ProtectedRoute>}
      />
      <Route
        path="/profiling"
        element={<ProtectedRoute><DataProfiling /></ProtectedRoute>}
      />
      <Route
        path="/issues"
        element={<ProtectedRoute><Issues /></ProtectedRoute>}
      />
      <Route
        path="/anomalies"
        element={<ProtectedRoute><Anomalies /></ProtectedRoute>}
      />
      <Route
        path="/corrections"
        element={<ProtectedRoute><Corrections /></ProtectedRoute>}
      />
      <Route
        path="/explainability"
        element={<ProtectedRoute><Explainability /></ProtectedRoute>}
      />
      <Route
        path="/monitoring"
        element={<ProtectedRoute><Monitoring /></ProtectedRoute>}
      />
      <Route
        path="/rules"
        element={<ProtectedRoute><RuleEngine /></ProtectedRoute>}
      />
      <Route
        path="/chat"
        element={<ProtectedRoute><ChatWithDataset /></ProtectedRoute>}
      />
      <Route
        path="/reports"
        element={<ProtectedRoute><Reports /></ProtectedRoute>}
      />
      <Route
        path="/history"
        element={<ProtectedRoute><History /></ProtectedRoute>}
      />
      <Route
        path="/settings"
        element={<ProtectedRoute><Settings /></ProtectedRoute>}
      />
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
      />
    </Routes>
  );
};

export default AppRoutes;
