import React, { useContext } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../../context/DatasetContext';
import { Database, User, LogOut, Bell, ShieldCheck, Sparkles } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { filename } = useContext(DatasetContext) || {};
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between shrink-0">
      {/* Brand & Workspace Indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => navigate('/dashboard')}>
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-base text-gray-900 tracking-tight leading-none">DataQuality AI</h1>
            <span className="text-xs text-gray-500 font-medium">Enterprise Intelligence</span>
          </div>
        </div>

        {filename && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-xs font-medium text-blue-700">
            <Database className="w-3.5 h-3.5" />
            <span>Active Dataset:</span>
            <span className="font-semibold">{filename}</span>
          </div>
        )}
      </div>

      {/* Global Actions & User Profile */}
      <div className="flex items-center gap-4">
        <button className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors relative" title="Notifications">
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-blue-600 absolute top-1.5 right-1.5"></span>
        </button>

        <div className="h-6 w-px bg-gray-200"></div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-700 font-semibold text-xs">
              {user?.username?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs font-semibold text-gray-900 leading-tight">{user?.username || user?.email || 'User'}</p>
              <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">{user?.role || 'ANALYST'}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
