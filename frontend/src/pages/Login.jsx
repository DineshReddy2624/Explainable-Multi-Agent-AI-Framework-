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

  const { login, register, forgotPassword, resetPassword } = useAuth();
  const navigate = useNavigate();

  const handleModeChange = (mode) => {
    setAuthMode(mode);
    setErrorMsg('');
    setSuccessMsg('');
    setResetStep(1);
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
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="johndoe"
                    value={username}
                    onChange={e => setUsername(e.target.value)}
                    required
                    className="input pl-9"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Organization Name</label>
                <div className="relative">
                  <Building className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Acme Analytics Corp"
                    value={orgName}
                    onChange={e => setOrgName(e.target.value)}
                    className="input pl-9"
                  />
                </div>
              </div>
            </>
          )}

          {(authMode !== 'FORGOT_PASSWORD' || resetStep === 1) && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  placeholder="analyst@enterprise.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  className="input pl-9"
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
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  className="input pl-9"
                />
              </div>
            </div>
          )}

          {authMode === 'REGISTER' && (
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                  className="input pl-9"
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
