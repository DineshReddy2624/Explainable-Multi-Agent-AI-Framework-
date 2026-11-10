import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Sparkles, Mail, Lock, User, Building, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';

const Login = () => {
  const [authMode, setAuthMode] = useState('SIGN_IN'); // 'SIGN_IN' | 'REGISTER' | 'FORGOT_PASSWORD'
  const [resetStep, setResetStep] = useState(1);

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [resetCode, setResetCode] = useState('');

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, register, loginWithOAuth, forgotPassword, resetPassword } = useAuth();
  const navigate = useNavigate();

  const handleModeChange = (mode) => {
    setAuthMode(mode);
    setErrorMsg('');
    setSuccessMsg('');
    setResetStep(1);
  };

  const handleOAuthLogin = async (provider) => {
    setErrorMsg('');
    setSuccessMsg('');
    setLoading(true);
    const res = await loginWithOAuth(provider);
    setLoading(false);
    if (res.success && !res.redirecting) {
      navigate('/dashboard');
    } else if (!res.success) {
      setErrorMsg(res.error || `Failed to authenticate with ${provider} OAuth`);
    }
  };




  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (authMode === 'REGISTER') {
      if (password !== confirmPassword) {
        setErrorMsg('Passwords do not match');
        return;
      }
      setLoading(true);
      const res = await register(username, email, password, orgName);
      setLoading(false);
      if (res.success) {
        navigate('/dashboard');
      } else {
        setErrorMsg(res.error || 'Registration failed');
      }
    } else if (authMode === 'SIGN_IN') {
      setLoading(true);
      const res = await login(email, password);
      setLoading(false);
      if (res.success) {
        navigate('/dashboard');
      } else {
        setErrorMsg(res.error || 'Invalid credentials');
      }
    } else if (authMode === 'FORGOT_PASSWORD') {
      if (resetStep === 1) {
        setLoading(true);
        const res = await forgotPassword(email);
        setLoading(false);
        if (res.success) {
          setSuccessMsg(`Verification code sent to ${email}. Please check your inbox.`);
          setResetStep(2);
        } else {
          setErrorMsg(res.error || 'Failed to send verification email');
        }
      } else {
        setLoading(true);
        const res = await resetPassword(email, resetCode, password);
        setLoading(false);
        if (res.success) {
          setSuccessMsg('Password reset successfully! Please sign in with your new password.');
          setTimeout(() => handleModeChange('SIGN_IN'), 2000);
        } else {
          setErrorMsg(res.error || 'Invalid verification code');
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-2xl shadow-sm p-8">
        {/* Header Branding */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white mx-auto mb-3 shadow-sm">
            <Sparkles className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 tracking-tight">DataQuality AI</h1>
          <p className="text-xs text-gray-500 font-medium mt-1">
            {authMode === 'REGISTER' && 'Create your enterprise workspace'}
            {authMode === 'SIGN_IN' && 'Sign in to access your dataset workspace'}
            {authMode === 'FORGOT_PASSWORD' && (resetStep === 1 ? 'Reset your password' : 'Verify reset code')}
          </p>
        </div>

        {/* Notifications */}
        {errorMsg && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-6 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {authMode === 'REGISTER' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Username</label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="johndoe"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    required
                    className="input !pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Organization Name</label>
                <div className="relative">
                  <Building className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="Acme Analytics Corp"
                    value={orgName}
                    onChange={e => setOrgName(e.target.value)}
                    className="input !pl-10"
                  />
                </div>
              </div>
            </>
          )}

          {(authMode !== 'FORGOT_PASSWORD' || resetStep === 1) && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                <input
                  type="email"
                  placeholder="analyst@enterprise.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  className="input !pl-10"
                />
              </div>
            </div>
          )}

          {authMode === 'FORGOT_PASSWORD' && resetStep === 2 && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Verification Code</label>
              <input
                type="text"
                placeholder="123456"
                value={resetCode}
                onChange={e => setResetCode(e.target.value)}
                required
                className="input text-center font-mono tracking-widest text-base"
              />
            </div>
          )}

          {(authMode !== 'FORGOT_PASSWORD' || resetStep === 2) && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-xs font-semibold text-gray-700">
                  {authMode === 'FORGOT_PASSWORD' ? 'New Password' : 'Password'}
                </label>
                {authMode === 'SIGN_IN' && (
                  <button
                    type="button"
                    onClick={() => handleModeChange('FORGOT_PASSWORD')}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  className="input !pl-10"
                />
              </div>
            </div>
          )}

          {authMode === 'REGISTER' && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                  className="input !pl-10"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full btn btn-primary py-2.5 mt-2 flex items-center justify-center gap-2 font-semibold text-sm"
          >
            <span>
              {loading
                ? 'Authenticating...'
                : authMode === 'REGISTER'
                ? 'Create Account'
                : authMode === 'SIGN_IN'
                ? 'Sign In'
                : resetStep === 1
                ? 'Send Code'
                : 'Reset Password'}
            </span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* OAuth SSO Section */}
        {authMode !== 'FORGOT_PASSWORD' && (
          <div className="mt-6">
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-[11px] uppercase tracking-wider">
                <span className="bg-white px-3 text-gray-500 font-semibold">Or continue with</span>
              </div>
            </div>

            <div>
              <button
                type="button"
                onClick={() => handleOAuthLogin('google')}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2.5 py-2.5 px-4 border border-gray-200 rounded-xl hover:bg-slate-50 transition text-xs font-semibold text-gray-700 shadow-sm"
              >
                <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                </svg>
                <span>Continue with Google</span>
              </button>
            </div>
          </div>
        )}


        {/* Footer Links */}
        <div className="mt-6 pt-6 border-t border-gray-200 text-center">
          <p className="text-xs text-gray-600">
            {authMode === 'REGISTER' && (
              <>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => handleModeChange('SIGN_IN')}
                  className="text-blue-600 hover:text-blue-800 font-semibold"
                >
                  Sign In
                </button>
              </>
            )}
            {authMode === 'SIGN_IN' && (
              <>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => handleModeChange('REGISTER')}
                  className="text-blue-600 hover:text-blue-800 font-semibold"
                >
                  Create Account
                </button>
              </>
            )}
            {authMode === 'FORGOT_PASSWORD' && (
              <button
                type="button"
                onClick={() => handleModeChange('SIGN_IN')}
                className="text-blue-600 hover:text-blue-800 font-semibold"
              >
                Back to Sign In
              </button>
            )}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
