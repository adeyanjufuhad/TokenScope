import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-[#E5E7EB] h-[56px] px-4 md:px-8">
      <div className="max-w-[1200px] mx-auto h-full flex items-center justify-between">
        {/* Left Side: Brand Wordmark & Pill Badge */}
        <div 
          onClick={() => navigate('/')} 
          className="flex items-center space-x-3 cursor-pointer select-none group"
        >
          <div className="flex items-center space-x-2.5">
            <img src="/logo.jpg" alt="TokenScope Logo" className="w-6 h-6 rounded-full object-cover shrink-0" />
            <span 
              className="text-[15px] font-bold text-[#0A0A0A] tracking-[0.08em]"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              TOKENSCOPE
            </span>
          </div>
          <span 
            className="hidden sm:inline-flex items-center px-2.5 py-0.5 text-[11px] font-normal text-[#6B7280] bg-[#F3F4F6] rounded-full"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            v1.0 — Solana Mainnet
          </span>
        </div>

        {/* Right Side: RPC Sync & Network */}
        <div className="hidden sm:flex items-center space-x-3 text-[13px] text-[#6B7280]">
          <div className="flex items-center space-x-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] shrink-0 animate-pulse" />
            <span style={{ fontFamily: 'Inter, sans-serif' }}>RPC Synced</span>
          </div>
          <div className="w-[1px] h-3.5 bg-[#E5E7EB]" />
          <span style={{ fontFamily: 'Inter, sans-serif' }}>Mainnet</span>
        </div>
      </div>
    </header>
  );
}
