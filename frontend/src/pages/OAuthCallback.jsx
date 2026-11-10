import React, { useEffect, useState, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import Loader from '../components/common/Loader';
import { AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react';

const OAuthCallback = () => {
  const [statusMsg, setStatusMsg] = useState('Verifying OAuth Identity & Exchanging Tokens...');
  const [errorMsg, setErrorMsg] = useState('');
  const { verifyOAuthCallback } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const processCallback = async () => {
      // 1. Parse Query params (Google Authorization Code flow: ?code=...&state=...)
      const queryParams = new URLSearchParams(location.search);
      const authCode = queryParams.get('code');
      const oauthError = queryParams.get('error');
      const errorDescription = queryParams.get('error_description');

      // 2. Parse Hash params (Implicit flow: #access_token=... or #id_token=...)
      const hashParams = new URLSearchParams(location.hash.replace(/^#/, ''));
      const accessToken = hashParams.get('access_token');
      const idToken = hashParams.get('id_token');
      const hashError = hashParams.get('error');

      // Check for cancelled or error response from Google
      const error = oauthError || hashError;
      if (error) {
        if (error === 'access_denied') {
          setErrorMsg('Google Sign-In was cancelled or access was denied.');
        } else {
          setErrorMsg(`Google authentication error: ${errorDescription || error}`);
        }
        return;
      }

      if (!authCode && !accessToken && !idToken) {
        setErrorMsg('No authorization code or token received from Google.');
        return;
      }

      setStatusMsg('Authenticating with Google OAuth...');

      const res = await verifyOAuthCallback({
        provider: 'google',
        code: authCode,
        access_token: accessToken,
        id_token: idToken
      });

      if (res.success) {
        setStatusMsg('Google Sign-In Successful! Redirecting to Workspace Dashboard...');
        setTimeout(() => {
          if (window.opener && !window.opener.closed) {
            try {
              window.opener.location.href = '/dashboard';
              window.close();
            } catch (e) {
              navigate('/dashboard');
            }
          } else {
            navigate('/dashboard');
          }
        }, 1000);
      } else {
        setErrorMsg(res.error || 'Failed to complete Google OAuth authentication.');
      }
    };

    processCallback();
  }, [location, navigate, verifyOAuthCallback]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-2xl shadow-sm p-8 text-center space-y-6">
        <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mx-auto shadow-sm">
          <ShieldCheck className="w-8 h-8" />
        </div>

        {!errorMsg ? (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-gray-900">{statusMsg}</h2>
            <Loader label="Securing session keys & verifying JWT tokens..." />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center justify-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => navigate('/login')}
              className="btn btn-primary btn-sm flex items-center justify-center mx-auto font-semibold"
            >
              Return to Sign In Page
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;
