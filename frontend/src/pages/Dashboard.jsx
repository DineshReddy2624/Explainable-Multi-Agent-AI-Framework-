import React, { useContext } from 'react';
import { DatasetContext } from '../context/DatasetContext';
import QualityCard from '../components/dashboard/QualityCard';
import MetricCard from '../components/dashboard/MetricCard';
import QualityGauge from '../components/dashboard/QualityGauge';
import DashboardChart from '../components/dashboard/DashboardChart';
import {
  Database,
  BarChart3,
  AlertTriangle,
  Wand2,
  Sparkles,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  Activity,
  Layers
} from 'lucide-react';

const Dashboard = () => {
  const { filename, analysis } = useContext(DatasetContext);

  const totalRows = analysis?.total_rows ? analysis.total_rows.toLocaleString() : '510';
  const totalCols = analysis?.total_cols ? analysis.total_cols : '8';
  const overallScore = analysis?.quality_scores?.overall_score ?? 98.4;
  const missingCount = analysis?.total_missing_cells ?? 0;
  const anomalyCount = analysis?.anomalies ? analysis.anomalies.length : 0;
  const formatCount = analysis?.format_issues ? analysis.format_issues.length : 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Executive Page Header - 100% Informational */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 px-6 py-5 rounded-2xl border border-indigo-500/20 shadow-lg text-white">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-blue-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-500/20">
            <Activity className="w-6 h-6 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl font-black text-white tracking-tight leading-snug">Data Intelligence Executive Dashboard</h2>
              <span className="px-3 py-0.5 text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full flex items-center gap-1.5 shrink-0">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                System Operational
              </span>
            </div>
            <p className="text-xs font-medium text-slate-300 mt-1">
              {filename 
                ? `Active Workspace Monitoring: '${filename}' (${totalRows} rows, ${totalCols} columns)`
                : 'Enterprise data quality benchmarks, statistical profiling, and automated multi-agent governance.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 bg-slate-800/90 border border-indigo-500/30 rounded-xl px-4 py-2 shadow-inner">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <div className="text-left">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">AI Agent Engines</span>
              <span className="text-xs font-black text-emerald-400">4 Active Workers</span>
            </div>
          </div>
        </div>
      </div>

      {/* Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <QualityCard
          score={overallScore}
          status={overallScore >= 85 ? 'Optimal' : overallScore >= 70 ? 'Warning' : 'Critical'}
        />
        <MetricCard
          title="Monitored Workspace Capacity"
          value={filename ? `${totalRows} Rows` : '8 Datasets'}
          subtitle={filename ? `${totalCols} columns profile active` : '500+ records processed'}
          icon={Database}
          color="text-blue-600"
          bg="bg-blue-50"
        />
        <MetricCard
          title="Statistical Anomalies"
          value={`${anomalyCount}`}
          subtitle={anomalyCount === 0 ? 'Zero critical outliers' : 'Anomalies isolated'}
          icon={AlertTriangle}
          color={anomalyCount === 0 ? 'text-emerald-600' : 'text-amber-600'}
          bg={anomalyCount === 0 ? 'bg-emerald-50' : 'bg-amber-50'}
        />
        <MetricCard
          title="Completeness & Integrity"
          value={`${missingCount + formatCount === 0 ? '100%' : missingCount + formatCount + ' Nulls'}`}
          subtitle={missingCount === 0 ? 'Zero missing values' : 'Remediation available'}
          icon={Wand2}
          color={missingCount + formatCount === 0 ? 'text-emerald-600' : 'text-indigo-600'}
          bg={missingCount + formatCount === 0 ? 'bg-emerald-50' : 'bg-indigo-50'}
        />
      </div>

      {/* Analytics Visual Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DashboardChart />
        </div>
        <div>
          <QualityGauge value={overallScore} />
        </div>
      </div>

      {/* Pure Informational Executive Platform Overview */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Multi-Agent Intelligence Platform Architecture</h3>
          </div>
          <span className="text-[11px] font-semibold text-slate-400 bg-slate-50 border border-slate-200 rounded-full px-3 py-1">
            Status: Fully Synchronized
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">
                01
              </span>
              <ShieldCheck className="w-4 h-4 text-blue-600" />
            </div>
            <h4 className="text-xs font-bold text-slate-900">Quality Profiling Engine</h4>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Automated schema detection, null cell counting, data type inference, and statistical entropy evaluation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs">
                02
              </span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <h4 className="text-xs font-bold text-slate-900">Anomaly Isolation Forest</h4>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Z-score statistical bounds checking, Isolation Forest outlier flagging, and numerical range verification.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                03
              </span>
              <Wand2 className="w-4 h-4 text-indigo-600" />
            </div>
            <h4 className="text-xs font-bold text-slate-900">Deterministic Imputation</h4>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Rule-based value remediation, mean/mode statistical imputation, and duplicate record deduplication.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">
                04
              </span>
              <Sparkles className="w-4 h-4 text-emerald-600" />
            </div>
            <h4 className="text-xs font-bold text-slate-900">Domain Analytical Chat</h4>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Natural language SQL routing across Sales, HR, Healthcare, E-Commerce, Logistics, and Finance domains.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
