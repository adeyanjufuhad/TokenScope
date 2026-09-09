import React from 'react';

export default function VerdictBadge({ verdict, className = '' }) {
  const v = (verdict || '').toUpperCase();

  let styleClass = 'bg-[#FAFAFA] text-[#6B7280] border border-[#E5E7EB]';
  let label = verdict || 'Unknown';

  if (v === 'SAFE') {
    styleClass = 'bg-[#F0FDF4] text-[#166534] border border-[#BBF7D0]';
    label = 'Safe';
  } else if (v === 'CAUTION') {
    styleClass = 'bg-[#FFFBEB] text-[#92400E] border border-[#FCD34D]';
    label = 'Caution';
  } else if (v === 'HIGH RISK') {
    styleClass = 'bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5]';
    label = 'High Risk';
  } else if (v === 'LIKELY RUG') {
    styleClass = 'bg-[#0A0A0A] text-[#FFFFFF] border-0';
    label = 'Likely Rug';
  }

  return (
    <span
      className={`inline-flex items-center justify-center px-3 py-1 rounded-[6px] text-[13px] font-semibold select-none leading-none ${styleClass} ${className}`}
      style={{ fontFamily: 'Inter, sans-serif' }}
    >
      {label}
    </span>
  );
}
