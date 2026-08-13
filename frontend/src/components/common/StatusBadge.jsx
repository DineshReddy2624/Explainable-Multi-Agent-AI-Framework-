import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, XCircle, Info } from 'lucide-react';

const StatusBadge = ({ status = 'QUEUED', label }) => {
  const norm = String(status).toUpperCase();

  let badgeClass = 'badge-neutral';
  let Icon = Info;
  let text = label || status;

  if (norm === 'SUCCESS' || norm === 'COMPLETED' || norm === 'OPTIMAL' || norm === 'PROFILED' || norm === 'CLEANED') {
    badgeClass = 'badge-success';
    Icon = CheckCircle2;
  } else if (norm === 'RUNNING' || norm === 'PROCESSING' || norm === 'INGESTED') {
    badgeClass = 'badge-info';
    Icon = Clock;
  } else if (norm === 'QUEUED' || norm === 'WARNING') {
    badgeClass = 'badge-warning';
    Icon = AlertTriangle;
  } else if (norm === 'FAILED' || norm === 'CRITICAL' || norm === 'ERROR') {
    badgeClass = 'badge-danger';
    Icon = XCircle;
  }

  return (
    <span className={`badge ${badgeClass}`}>
      <Icon className="w-3 h-3" />
      <span>{text}</span>
    </span>
  );
};

export default StatusBadge;
