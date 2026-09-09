import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Users, Cpu, ArrowRight, AlertCircle } from 'lucide-react';
import Header from '../components/Header';
import VerdictBadge from '../components/VerdictBadge';
import { auditToken } from '../services/api';

const SAMPLE_TOKENS = [
  { label: 'BONK', type: 'Meme', address: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263' },
  { label: 'JUP', type: 'DeFi', address: 'JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN' },
  { label: 'USDC', type: 'Stable', address: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' },
  { label: 'RAY', type: 'DEX', address: '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R' },
];

export default function Home() {
  const [mintAddress, setMintAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleAudit = async (e) => {
    if (e) e.preventDefault();
    const cleanAddress = mintAddress.trim();
    if (!cleanAddress) {
      setError('Please enter a valid Solana mint address.');
      return;
    }
    if (cleanAddress.length < 32 || cleanAddress.length > 44) {
      setError('Invalid address length. Solana mint addresses are 32 to 44 characters.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await auditToken(cleanAddress);
      const reportId = res.report_id;
      
      if (res.status === 'completed' && res.cached) {
        navigate(`/report/${reportId}`);
      } else {
        navigate(`/loading/${reportId}`, { state: { mintAddress: cleanAddress } });
      }
    } catch (err) {
      setError(err.message || 'Failed to initiate token audit.');
      setLoading(false);
    }
  };

  const handleSelectSample = (addr) => {
    setMintAddress(addr);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-white text-[#0A0A0A] flex flex-col justify-between">
      {/* Redesigned Institutional Header */}
      <Header />

      {/* Main Two-Column Hero Container */}
      <main className="flex-1 max-w-[1200px] mx-auto px-4 sm:px-8 py-10 md:py-16 w-full flex flex-col justify-center">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 lg:gap-14 items-center">
          
          {/* Left Column (55% on desktop) */}
          <div className="md:col-span-7 flex flex-col items-start">
            {/* Pill Tag */}
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#F0FDF4] text-[#166534] border border-[#BBF7D0] rounded-full text-[12px] font-medium mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#166534] animate-pulse" />
              <span>Solana Token Intelligence</span>
            </div>

            {/* Main Headline */}
            <h1 
              className="text-[32px] md:text-[44px] font-bold text-[#0A0A0A] leading-[1.15] tracking-tight max-w-[480px]"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Audit any Solana token in seconds.
            </h1>

            {/* Subheadline */}
            <p 
              className="text-[16px] md:text-[17px] text-[#6B7280] font-normal leading-[1.6] max-w-[440px] mt-4"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Paste a token address. Get a full institutional-grade risk report covering security, holder concentration, market health, and AI-generated risk synthesis.
            </p>

            {/* Input Form Area */}
            <form onSubmit={handleAudit} className="w-full max-w-[480px] mt-8">
              <div>
                <label 
                  htmlFor="mint-input"
                  className="block text-[13px] font-medium text-[#374151] mb-1.5"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  Token mint address
                </label>
                <input
                  id="mint-input"
                  type="text"
                  value={mintAddress}
                  onChange={(e) => {
                    setMintAddress(e.target.value.trim());
                    setError(null);
                  }}
                  placeholder="e.g. EPjFWdd5AufqSSqeM2qN..."
                  className="w-full h-[48px] bg-white text-[#0A0A0A] border-[1.5px] border-[#D1D5DB] rounded-[10px] px-4 font-mono text-[14px] placeholder:text-[#9CA3AF] focus:border-[#0A0A0A] focus:outline-none focus:ring-2 focus:ring-black/5 transition-all"
                  disabled={loading}
                  autoFocus
                />
                <p 
                  className="text-[12px] text-[#9CA3AF] mt-1.5"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  Supports any SPL token on Solana mainnet
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mt-3 flex items-start space-x-2 text-[13px] text-[#991B1B] bg-[#FEF2F2] border border-[#FCA5A5] rounded-[8px] p-3">
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Audit Button */}
              <div className="mt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full sm:w-auto h-[48px] px-7 bg-[#0A0A0A] hover:bg-[#1F2937] text-white text-[15px] font-medium rounded-[8px] transition-colors inline-flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer select-none"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  <span>{loading ? 'Auditing token...' : 'Audit token →'}</span>
                </button>
              </div>

              {/* Quick-test verified mints */}
              <div className="mt-6 pt-5 border-t border-[#F3F4F6]">
                <span className="text-[12px] text-[#9CA3AF] block mb-2 font-medium">
                  Quick-test verified mints:
                </span>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_TOKENS.map((sample) => (
                    <button
                      key={sample.label}
                      type="button"
                      onClick={() => handleSelectSample(sample.address)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1 bg-[#F9FAFB] hover:bg-[#F3F4F6] border border-[#E5E7EB] rounded-full text-[12px] text-[#374151] hover:text-[#0A0A0A] transition-colors cursor-pointer"
                    >
                      <span className="font-semibold">{sample.label}</span>
                      <span className="text-[11px] text-[#9CA3AF]">({sample.type})</span>
                    </button>
                  ))}
                </div>
              </div>
            </form>
          </div>

          {/* Right Column: Static Report Preview Card (45% on desktop, hidden on mobile <=768px) */}
          <div className="hidden md:block md:col-span-5">
            <div className="bg-white border border-[#E5E7EB] rounded-[12px] p-6 shadow-card max-w-[440px] ml-auto">
              {/* a) Header row */}
              <div className="flex items-center justify-between pb-4 border-b border-[#E5E7EB]">
                <div className="flex items-center space-x-2">
                  <span className="text-[16px] font-bold text-[#0A0A0A]">Jupiter</span>
                  <span className="text-[14px] text-[#6B7280]">$JUP</span>
                </div>
                <VerdictBadge verdict="CAUTION" />
              </div>

              {/* c) Large score display */}
              <div className="mt-5">
                <div className="flex items-baseline space-x-1.5">
                  <span className="font-mono text-[48px] font-bold text-[#0A0A0A] leading-none">
                    88
                  </span>
                  <span className="text-[12px] text-[#9CA3AF]">
                    / 100 overall trust score
                  </span>
                </div>
              </div>

              {/* d) Horizontal progress-bar score visualization (5 segments) */}
              <div className="mt-5 pt-4 border-t border-[#F3F4F6]">
                <div className="grid grid-cols-5 gap-2 text-center">
                  {[
                    { label: 'Sec', score: 100, fill: '100%' },
                    { label: 'Hold', score: 55, fill: '55%' },
                    { label: 'Mkt', score: 70, fill: '70%' },
                    { label: 'Cont', score: 90, fill: '90%' },
                    { label: 'Soc', score: 65, fill: '65%' },
                  ].map((seg) => (
                    <div key={seg.label} className="space-y-1">
                      <span className="text-[11px] font-medium text-[#6B7280] block">
                        {seg.label}
                      </span>
                      <div className="h-1.5 w-full bg-[#E5E7EB] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-[#0A0A0A] rounded-full" 
                          style={{ width: seg.fill }}
                        />
                      </div>
                      <span className="font-mono text-[11px] font-semibold text-[#0A0A0A] block">
                        {seg.score}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* e) AI summary text block with left border */}
              <div className="mt-5 p-3.5 bg-[#F9FAFB] border-l-[3px] border-l-[#0A0A0A] rounded-r-[6px]">
                <p className="text-[13px] italic text-[#374151] leading-[1.6]">
                  "Primary risk: extreme holder concentration. Top 2 wallets control 50% of supply. Security authorities fully revoked."
                </p>
              </div>

              {/* f) Three small stat pills in a row */}
              <div className="mt-5 flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-[#F9FAFB] border border-[#E5E7EB] rounded-full text-[12px] text-[#374151]">
                  🔒 LP Locked
                </span>
                <span className="px-3 py-1 bg-[#F9FAFB] border border-[#E5E7EB] rounded-full text-[12px] text-[#374151]">
                  ✓ Mint Revoked
                </span>
                <span className="px-3 py-1 bg-[#F9FAFB] border border-[#E5E7EB] rounded-full text-[12px] text-[#374151]">
                  ⚠ High concentration
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* Below the two columns: 3 Feature Cards */}
        <div className="mt-16 md:mt-20 pt-10 border-t border-[#E5E7EB]">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Card 1 */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-5 md:p-6 hover:border-[#D1D5DB] transition-colors">
              <Shield size={20} className="text-[#0A0A0A] mb-3" />
              <h3 className="text-[15px] font-semibold text-[#0A0A0A] mb-1.5">
                Security analysis
              </h3>
              <p className="text-[14px] text-[#6B7280] leading-[1.5]">
                Mint authority, freeze authority, and liquidity pool lock status checked against deterministic rules.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-5 md:p-6 hover:border-[#D1D5DB] transition-colors">
              <Users size={20} className="text-[#0A0A0A] mb-3" />
              <h3 className="text-[15px] font-semibold text-[#0A0A0A] mb-1.5">
                Holder intelligence
              </h3>
              <p className="text-[14px] text-[#6B7280] leading-[1.5]">
                Top 10 wallet concentration mapped with whale dispersion scoring and AMM vault separation.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-5 md:p-6 hover:border-[#D1D5DB] transition-colors">
              <Cpu size={20} className="text-[#0A0A0A] mb-3" />
              <h3 className="text-[15px] font-semibold text-[#0A0A0A] mb-1.5">
                AI risk synthesis
              </h3>
              <p className="text-[14px] text-[#6B7280] leading-[1.5]">
                Gemini 2.0 Flash translates raw onchain data into plain-English verdicts. No jargon.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-[#E5E7EB] py-6 bg-[#FFFFFF] mt-12 px-4 md:px-8">
        <div className="max-w-[1200px] mx-auto flex flex-col sm:flex-row items-center justify-between text-[12px] text-[#9CA3AF] gap-2">
          <span>TokenScope — Solana onchain risk intelligence</span>
          <span>© {new Date().getFullYear()} TokenScope. Institutional Due Diligence Platform.</span>
        </div>
      </footer>
    </div>
  );
}
