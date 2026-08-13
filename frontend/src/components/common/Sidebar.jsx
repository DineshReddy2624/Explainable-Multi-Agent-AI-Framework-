import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  BarChart3,
  AlertCircle,
  AlertTriangle,
  Wand2,
  MessageSquare,
  FileText,
  Clock
} from 'lucide-react';

const navigationGroups = [
  {
    title: 'OVERVIEW',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard }
    ]
  },
  {
    title: 'DATA WORKSPACE',
    items: [
      { label: 'Upload & Analyze', path: '/upload', icon: Upload },
      { label: 'Data Profiling', path: '/profiling', icon: BarChart3 },
      { label: 'Quality Issues', path: '/issues', icon: AlertCircle },
      { label: 'Anomaly Detection', path: '/anomalies', icon: AlertTriangle },
      { label: 'AI Remediation', path: '/corrections', icon: Wand2 }
    ]
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { label: 'AI Dataset Chat', path: '/chat', icon: MessageSquare },
      { label: 'Executive Reports', path: '/reports', icon: FileText },
      { label: 'Background Jobs', path: '/monitoring', icon: Clock }
    ]
  }
];

const Sidebar = () => {
  const location = useLocation();

  return (
    <aside className="w-60 bg-white border-r border-gray-200 py-4 px-3 flex flex-col gap-6 shrink-0 overflow-y-auto">
      {navigationGroups.map((group, gIdx) => (
        <div key={gIdx} className="flex flex-col gap-1">
          <h3 className="px-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
            {group.title}
          </h3>
          <nav className="flex flex-col gap-0.5 mt-1">
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      ))}
    </aside>
  );
};

export default Sidebar;
