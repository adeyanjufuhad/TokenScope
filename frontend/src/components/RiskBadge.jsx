import React from 'react';
import VerdictBadge from './VerdictBadge';

export default function RiskBadge({ verdict, className = '' }) {
  return <VerdictBadge verdict={verdict} className={className} />;
}
