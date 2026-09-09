import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Copy, Check, ExternalLink, Code, Printer, AlertTriangle } from 'lucide-react';
import { getReport, truncateAddress } from '../services/api';
import VerdictBadge from '../components/VerdictBadge';
import PillarCard from '../components/PillarCard';
import AISummaryCard from '../components/AISummaryCard';
import HolderChart from '../components/HolderChart';
import PriceSparkline from '../components/PriceSparkline';
import ShareButton from '../components/ShareButton';

export default function Report() {
  const { report_id } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedAddr, setCopiedAddr] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function fetchReportData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getReport(report_id);

        if (!isMounted) return;

        if (data.status === 'processing') {
          navigate(`/loading/${report_id}`, { replace: true });
          return;
        }

        setReport(data);
      } catch (err) {
        if (!isMounted) return;
        setError(err.message || 'Report not found or unavailable.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchReportData();

    return () => {
      isMounted = false;
    };
  }, [report_id, navigate]);

  const copyMint = () => {
    if (!report?.mint_address) return;
    navigator.clipboard.writeText(report.mint_address);
    setCopiedAddr(true);
    setTimeout(() => setCopiedAddr(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6">
        <div className="w-8 h-8 rounded-full border-2 border-[#0A0A0A] border-t-transparent animate-spin-custom mb-3"></div>
        <p className="text-[14px] text-[#6B7280]">Loading risk audit report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 text-center">
        <div className="w-10 h-10 rounded-full bg-[#FEF2F2] flex items-center justify-center text-[#DC2626] mb-4">
          <AlertTriangle size={20} />
        </div>
        <h2 className="text-[20px] font-bold text-[#0A0A0A] mb-2">
          Report not found
        </h2>
        <p className="text-[14px] text-[#6B7280] max-w-sm mb-6">
          {error || 'Unable to retrieve this report. Please verify the report ID or run a new audit.'}
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-5 py-2.5 bg-[#0A0A0A] hover:bg-[#1F2937] text-white text-[13px] font-medium rounded-[8px] transition-colors cursor-pointer"
        >
          ← Return to audit terminal
        </button>
      </div>
    );
  }

  const {
    token_name = 'Unknown Token',
    token_symbol = 'TOKEN',
    mint_address = '',
    overall_score = 0,
    verdict = 'CAUTION',
    pillars = {},
    ai_summary = '',
    asset_classification = report.pillars?.asset_classification || 'STANDARD_SPL',
    issuer = report.pillars?.issuer || null,
    generated_at = ''
  } = report;

  const cleanSymbol = String(token_symbol || 'TOKEN').replace(/^\$+/, '');

  const topHolders = pillars.holders?.top_holders || [];
  const priceHistory = pillars.market?.price_history || [];
  const liquidityUsd = pillars.market?.liquidity_usd || 0;
  const volume24h = pillars.market?.volume_24h || 0;
  const marketCapUsd = pillars.market?.market_cap_usd || 0;

  const uniqueTraders24h = pillars.market?.unique_traders_24h;
  const trades24h = pillars.market?.trades_24h;
  const holdersCount = pillars.holders?.total_holders_count;

  let traderMetricLabel = 'Unique Traders (24h)';
  let traderMetricValue = 'N/A';

  if (uniqueTraders24h !== null && uniqueTraders24h !== undefined) {
    traderMetricLabel = 'Unique Traders (24h)';
    traderMetricValue = Number(uniqueTraders24h).toLocaleString();
  } else if (trades24h !== null && trades24h !== undefined) {
    traderMetricLabel = 'Trades (24h)';
    traderMetricValue = Number(trades24h).toLocaleString();
  } else if (holdersCount !== null && holdersCount !== undefined) {
    traderMetricLabel = 'Total Holders';
    traderMetricValue = Number(holdersCount).toLocaleString();
  }

  // Format date e.g. "9 Sep 2026, 6:11 PM"
  const formattedDate = generated_at 
    ? new Date(generated_at).toLocaleString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
    : '';

  // 5 Breakdown segments with color determination
  const getScoreColor = (score) => {
    if (score >= 75) return '#059669';
    if (score >= 50) return '#D97706';
    return '#DC2626';
  };

  const segments = [
    { label: 'Security', score: pillars.security?.score ?? 0, weight: '35% weight' },
    { label: 'Holders', score: pillars.holders?.score ?? 0, weight: '25% weight' },
    { label: 'Market', score: pillars.market?.score ?? 0, weight: '15% weight' },
    { label: 'Contract', score: pillars.contract?.score ?? 0, weight: '10% weight' },
    { label: 'Social', score: pillars.social?.score ?? 0, weight: '15% weight' },
  ];

  return (
    <div className="min-h-screen bg-white text-[#0A0A0A] flex flex-col justify-between">
      
      {/* 1. REPORT HEADER SECTION */}
      <header className="w-full bg-white border-b border-[#E5E7EB] px-4 md:px-8 py-4 sticky top-0 z-40">
        <div className="max-w-[1100px] mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="text-[13px] text-[#6B7280] hover:text-[#0A0A0A] transition-colors inline-flex items-center space-x-1 cursor-pointer"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            <span>← Audit another token</span>
          </button>

          <div className="flex items-center space-x-2 sm:space-x-3">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="px-3.5 py-1.5 border border-[#E5E7EB] hover:border-[#D1D5DB] bg-white text-[#374151] rounded-[6px] text-[13px] font-medium transition-colors cursor-pointer"
            >
              JSON
            </button>

            <button
              onClick={handlePrint}
              className="px-3.5 py-1.5 border border-[#E5E7EB] hover:border-[#D1D5DB] bg-white text-[#374151] rounded-[6px] text-[13px] font-medium transition-colors cursor-pointer"
            >
              Print
            </button>

            <ShareButton />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="w-full flex-1 pb-16">
        
        {/* Raw JSON Drawer if toggled */}
        {showRawJson && (
          <div className="max-w-[1100px] mx-auto px-4 md:px-8 my-6">
            <div className="border border-[#E5E7EB] rounded-[10px] p-5 bg-[#F9FAFB]">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#E5E7EB]">
                <span className="text-[13px] font-semibold text-[#0A0A0A]">
                  Raw audit payload (Report ID: {report_id})
                </span>
                <button
                  onClick={() => setShowRawJson(false)}
                  className="text-[12px] text-[#6B7280] hover:text-[#0A0A0A]"
                >
                  Close
                </button>
              </div>
              <pre className="font-mono text-[12px] text-[#374151] overflow-x-auto max-h-80 leading-relaxed">
                {JSON.stringify(report, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* 2. TOKEN IDENTITY BLOCK */}
        <section className="max-w-[1100px] mx-auto px-4 md:px-8 py-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            
            {/* Left Identity Column */}
            <div className="space-y-3">
              <div className="flex flex-wrap items-baseline gap-3">
                <h1 
                  className="text-[28px] md:text-[32px] font-bold text-[#0A0A0A] leading-tight"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  {token_name}
                </h1>
                <span 
                  className="text-[18px] md:text-[20px] font-normal text-[#6B7280]"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  ${cleanSymbol}
                </span>

                {asset_classification === 'STABLECOIN' && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-[4px] text-[12px] font-medium bg-[#EFF6FF] text-[#1D4ED8] border border-[#DBEAFE]">
                    Regulated Stablecoin {issuer ? `· ${issuer}` : ''}
                  </span>
                )}
                {asset_classification === 'WRAPPED' && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-[4px] text-[12px] font-medium bg-[#F3F4F6] text-[#374151] border border-[#E5E7EB]">
                    Canonical Wrapped Asset {issuer ? `· ${issuer}` : ''}
                  </span>
                )}
              </div>

              {/* Mint Address Pill + Solscan + Audited Date */}
              <div className="flex flex-wrap items-center gap-3 text-[12px]">
                <div className="inline-flex items-center space-x-2 bg-[#F9FAFB] border border-[#E5E7EB] rounded-[6px] px-3 py-1">
                  <span className="font-mono text-[12px] text-[#0A0A0A]">
                    {truncateAddress(mint_address, 6)}
                  </span>
                  <button
                    onClick={copyMint}
                    className="text-[#6B7280] hover:text-[#0A0A0A] p-0.5 cursor-pointer"
                    title="Copy mint address"
                  >
                    {copiedAddr ? <Check size={12} className="text-[#059669]" /> : <Copy size={12} />}
                  </button>
                </div>

                <a
                  href={`https://solscan.io/token/${mint_address}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#6B7280] hover:text-[#0A0A0A] inline-flex items-center space-x-1"
                >
                  <span>Solscan</span>
                  <ExternalLink size={12} />
                </a>

                {formattedDate && (
                  <span className="text-[#9CA3AF] border-l border-[#E5E7EB] pl-3">
                    Audited {formattedDate}
                  </span>
                )}
              </div>
            </div>

            {/* Right Score & Verdict Display */}
            <div className="flex flex-col md:items-end">
              <div className="flex items-baseline space-x-1.5">
                <span className="font-mono text-[52px] md:text-[64px] font-bold text-[#0A0A0A] leading-none">
                  {overall_score}
                </span>
                <span className="font-mono text-[20px] md:text-[24px] text-[#9CA3AF]">
                  / 100
                </span>
              </div>

              <div className="mt-2">
                <VerdictBadge verdict={verdict} className="text-[14px] px-3.5 py-1.5" />
              </div>

              <span 
                className="text-[12px] text-[#9CA3AF] mt-1.5"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                Overall trust score
              </span>
            </div>

          </div>
        </section>

        {/* 3. SCORE BREAKDOWN BAR (Full Width Strip) */}
        <section className="w-full bg-[#FAFAFA] border-y border-[#E5E7EB] px-4 md:px-8 py-5">
          <div className="max-w-[1100px] mx-auto">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 md:gap-0 divide-y sm:divide-y-0 md:divide-x divide-[#E5E7EB]">
              {segments.map((seg, idx) => (
                <div key={seg.label} className={`space-y-1.5 ${idx > 0 ? 'md:pl-6' : ''} ${idx < segments.length - 1 ? 'md:pr-6' : ''}`}>
                  <span 
                    className="text-[11px] font-medium text-[#6B7280] uppercase tracking-[0.05em] block"
                    style={{ fontFamily: 'Inter, sans-serif' }}
                  >
                    {seg.label}
                  </span>
                  
                  {/* Progress Bar (height: 6px, bg: #E5E7EB, border-radius: 3px, width: 120px) */}
                  <div className="w-full max-w-[140px] h-[6px] bg-[#E5E7EB] rounded-[3px] overflow-hidden">
                    <div 
                      className="h-full rounded-[3px] transition-all duration-500"
                      style={{ 
                        width: `${Math.max(4, Math.min(100, seg.score))}%`,
                        backgroundColor: getScoreColor(seg.score)
                      }}
                    />
                  </div>

                  <div className="flex items-baseline space-x-2 pt-0.5">
                    <span className="font-mono text-[16px] font-semibold text-[#0A0A0A]">
                      {seg.score}
                    </span>
                    <span 
                      className="text-[11px] text-[#9CA3AF]"
                      style={{ fontFamily: 'Inter, sans-serif' }}
                    >
                      {seg.weight}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 4. AI SUMMARY CARD */}
        <section className="px-4 md:px-8">
          <AISummaryCard summary={ai_summary} />
        </section>

        {/* 5. 6-PILLAR GRID */}
        <section className="max-w-[1100px] mx-auto px-4 md:px-8 pt-4 pb-8">
          <div className="mb-5">
            <h2 
              className="text-[18px] font-semibold text-[#0A0A0A]"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Risk breakdown
            </h2>
            <p 
              className="text-[13px] text-[#9CA3AF] mt-0.5"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Weighted scoring across 6 independent audit pillars
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PillarCard
              title="1. Security & authorities"
              pillar={pillars.security}
            />
            <PillarCard
              title="2. Holder distribution"
              pillar={pillars.holders}
            />
            <PillarCard
              title="3. Market health & AMM"
              pillar={pillars.market}
            />
            <PillarCard
              title="4. Contract intelligence"
              pillar={pillars.contract}
            />
            <PillarCard
              title="5. Social validity"
              pillar={pillars.social}
            />
            <div className="bg-white border border-[#E5E7EB] rounded-[10px] p-5 md:p-6 shadow-card flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h3 
                    className="text-[14px] font-semibold text-[#0A0A0A]"
                    style={{ fontFamily: 'Inter, sans-serif' }}
                  >
                    6. Synthesized verdict
                  </h3>
                  <VerdictBadge verdict={verdict} />
                </div>
                <p 
                  className="text-[13px] text-[#374151] leading-[1.6] mt-4"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  Synthesized across onchain authority flags, liquidity pool solvency, insider whale concentration, and Gemini 2.0 Flash retail intelligence.
                </p>
              </div>

              <div className="mt-6 pt-3 border-t border-[#F3F4F6] flex items-center justify-between text-[12px]">
                <span className="text-[#9CA3AF]">Final synthesis:</span>
                <span className="font-semibold text-[#0A0A0A]">{verdict}</span>
              </div>
            </div>
          </div>
        </section>

        {/* 6. HOLDER DISTRIBUTION CHART */}
        <section className="max-w-[1100px] mx-auto px-4 md:px-8 py-6">
          <HolderChart holders={topHolders} />
        </section>

        {/* 7. PRICE HISTORY CHART (7 DAYS) */}
        <section className="max-w-[1100px] mx-auto px-4 md:px-8 py-6">
          <PriceSparkline prices={priceHistory} />
        </section>

        {/* 8. MARKET STATS ROW (4 METRIC CARDS) */}
        <section className="max-w-[1100px] mx-auto px-4 md:px-8 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Liquidity */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-4 sm:p-5">
              <span 
                className="text-[11px] font-medium text-[#9CA3AF] uppercase tracking-[0.05em] block"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                Liquidity (USD)
              </span>
              <div className="font-mono text-[20px] font-semibold text-[#0A0A0A] mt-1">
                ${liquidityUsd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
            </div>

            {/* 24h Volume */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-4 sm:p-5">
              <span 
                className="text-[11px] font-medium text-[#9CA3AF] uppercase tracking-[0.05em] block"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                24h Volume
              </span>
              <div className="font-mono text-[20px] font-semibold text-[#0A0A0A] mt-1">
                ${volume24h.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
            </div>

            {/* Market Cap */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-4 sm:p-5">
              <span 
                className="text-[11px] font-medium text-[#9CA3AF] uppercase tracking-[0.05em] block"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                Market Cap
              </span>
              <div className="font-mono text-[20px] font-semibold text-[#0A0A0A] mt-1">
                ${marketCapUsd > 0 ? marketCapUsd.toLocaleString(undefined, { maximumFractionDigits: 0 }) : 'N/A'}
              </div>
            </div>

            {/* Unique Traders / Activity */}
            <div className="bg-[#FAFAFA] border border-[#E5E7EB] rounded-[10px] p-4 sm:p-5">
              <span 
                className="text-[11px] font-medium text-[#9CA3AF] uppercase tracking-[0.05em] block"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                {traderMetricLabel}
              </span>
              <div className="font-mono text-[20px] font-semibold text-[#0A0A0A] mt-1">
                {traderMetricValue}
              </div>
            </div>
          </div>
        </section>

      </main>

      {/* 9. REPORT FOOTER */}
      <footer className="w-full bg-[#FAFAFA] border-t border-[#E5E7EB] px-4 md:px-8 py-5">
        <div className="max-w-[1100px] mx-auto flex flex-col sm:flex-row items-center justify-between text-[12px] text-[#9CA3AF] gap-2">
          <span>TokenScope — Solana onchain risk intelligence</span>
          <span className="font-mono text-[12px]">Report ID: {report_id}</span>
        </div>
      </footer>

    </div>
  );
}
