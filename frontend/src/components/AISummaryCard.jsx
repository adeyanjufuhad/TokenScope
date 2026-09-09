import React from 'react';

export default function AISummaryCard({ summary }) {
  if (!summary) return null;

  // Clean markdown asterisks from the displayed summary text
  const cleanedSummary = summary.replace(/\*\*/g, '').trim();

  return (
    <div 
      className="bg-white border border-[#E5E7EB] border-l-[3px] border-l-[#0A0A0A] rounded-r-[10px] rounded-l-none p-6 my-6 max-w-[1100px] mx-auto shadow-card"
    >
      {/* Header Row */}
      <div className="flex items-center justify-between">
        <span 
          className="text-[13px] font-semibold text-[#0A0A0A]"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          AI risk summary
        </span>
        <span 
          className="text-[11px] text-[#6B7280] bg-[#F3F4F6] rounded-full px-2.5 py-0.5"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Gemini 2.0 Flash
        </span>
      </div>

      {/* Summary Body */}
      <p 
        className="text-[15px] text-[#374151] leading-[1.7] mt-3"
        style={{ fontFamily: 'Inter, sans-serif' }}
      >
        {cleanedSummary}
      </p>

      {/* Footer Meta Row */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-[#9CA3AF] mt-4 pt-3 border-t border-[#F3F4F6] gap-2">
        <span style={{ fontFamily: 'Inter, sans-serif' }}>
          Target audience: retail due diligence
        </span>
        <span style={{ fontFamily: 'Inter, sans-serif' }}>
          Plain-English — no jargon
        </span>
      </div>
    </div>
  );
}
