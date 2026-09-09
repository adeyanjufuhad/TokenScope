import React, { useState } from 'react';

export default function PillarCard({ title, pillar }) {
  const [expanded, setExpanded] = useState(false);

  if (!pillar) return null;
  const score = pillar.score !== undefined ? pillar.score : 0;
  const rawFlags = pillar.flags || [];

  // Group flags: CRITICAL first, then WARNING, then INFO
  const criticalFlags = rawFlags.filter(f => (f.severity || '').toUpperCase() === 'CRITICAL');
  const warningFlags = rawFlags.filter(f => (f.severity || '').toUpperCase() === 'WARNING');
  const infoFlags = rawFlags.filter(f => (f.severity || '').toUpperCase() !== 'CRITICAL' && (f.severity || '').toUpperCase() !== 'WARNING');
  const sortedFlags = [...criticalFlags, ...warningFlags, ...infoFlags];

  const visibleFlags = expanded ? sortedFlags : sortedFlags.slice(0, 5);
  const remainingCount = sortedFlags.length - 5;

  // Score color system:
  // >= 75: #059669 (green)
  // 50-74: #D97706 (amber)
  // < 50: #DC2626 (red)
  let scoreColor = '#DC2626';
  if (score >= 75) {
    scoreColor = '#059669';
  } else if (score >= 50) {
    scoreColor = '#D97706';
  }

  const getDotColor = (severity) => {
    const s = (severity || '').toUpperCase();
    if (s === 'CRITICAL') return '#DC2626';
    if (s === 'WARNING') return '#D97706';
    return '#9CA3AF';
  };

  return (
    <div className="bg-white border border-[#E5E7EB] rounded-[10px] p-5 md:p-6 shadow-card hover:shadow-cardHover transition-shadow flex flex-col justify-between">
      <div>
        {/* Card Header */}
        <div className="flex items-center justify-between">
          <h3 
            className="text-[14px] font-semibold text-[#0A0A0A]"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {title}
          </h3>
          <span 
            className="text-[24px] font-bold font-mono"
            style={{ color: scoreColor }}
          >
            {score}
          </span>
        </div>

        {/* Score Bar */}
        <div className="w-full h-1 bg-[#E5E7EB] rounded-full my-3 overflow-hidden">
          <div 
            className="h-full rounded-full transition-all duration-500"
            style={{ 
              width: `${Math.max(3, Math.min(100, score))}%`,
              backgroundColor: scoreColor 
            }}
          />
        </div>

        {/* Flags List */}
        <div className="space-y-2 mt-4">
          {sortedFlags.length === 0 ? (
            <div className="flex items-center space-x-2 text-[13px] text-[#6B7280]">
              <span className="w-2 h-2 rounded-full bg-[#059669] shrink-0" />
              <span style={{ fontFamily: 'Inter, sans-serif' }}>No active risk flags detected</span>
            </div>
          ) : (
            visibleFlags.map((flag, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-[13px] leading-[1.45]">
                <span 
                  className="w-2 h-2 rounded-full shrink-0 mt-1.5"
                  style={{ backgroundColor: getDotColor(flag.severity) }}
                />
                <span 
                  className="text-[#374151]"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  {flag.label}
                </span>
              </div>
            ))
          )}

          {/* Collapsible "+ X more" toggle if more than 5 flags */}
          {remainingCount > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-[12px] font-medium text-[#6B7280] hover:text-[#0A0A0A] transition-colors pt-1 block cursor-pointer"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              {expanded ? 'Show fewer flags' : `+ ${remainingCount} more`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
