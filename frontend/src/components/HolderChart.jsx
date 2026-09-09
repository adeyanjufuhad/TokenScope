import React, { useEffect, useRef, useState } from 'react';
import { truncateAddress } from '../services/api';
import { ExternalLink, Copy, Check } from 'lucide-react';

export default function HolderChart({ holders = [] }) {
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const [copiedIdx, setCopiedIdx] = useState(null);

  const copyAddress = (addr, idx) => {
    if (!addr) return;
    navigator.clipboard.writeText(addr);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1500);
  };

  const top10 = (holders || []).slice(0, 10);
  const hasData = top10.length > 0;

  useEffect(() => {
    if (!hasData || !canvasRef.current) return;

    // Check for Chart constructor on window
    const Chart = window.Chart;
    if (!Chart) return;

    // Clean up existing instance before re-creating
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
      chartInstanceRef.current = null;
    }

    const labels = top10.map(h => {
      if (h.label) {
        return `${h.label} (${truncateAddress(h.owner || h.address, 3)})`;
      }
      return truncateAddress(h.owner || h.address, 4);
    });
    const dataValues = top10.map(h => h.percentage || 0);
    const backgroundColors = top10.map(h => h.exclude_from_concentration ? '#2563EB' : '#0A0A0A');

    const ctx = canvasRef.current.getContext('2d');
    chartInstanceRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            data: dataValues,
            backgroundColor: backgroundColors,
            borderRadius: 3,
            borderSkipped: false,
            barThickness: 14,
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: '#0A0A0A',
            titleColor: '#FFFFFF',
            bodyColor: '#FFFFFF',
            titleFont: { family: 'IBM Plex Mono', size: 12 },
            bodyFont: { family: 'IBM Plex Mono', size: 12 },
            padding: 10,
            cornerRadius: 6,
            displayColors: false,
            callbacks: {
              title: (items) => {
                const idx = items[0].dataIndex;
                const h = top10[idx];
                if (h?.label) {
                  return `${h.label} [${h.category || 'Known'}]`;
                }
                return h?.owner || h?.address || items[0].label;
              },
              label: (item) => {
                const idx = item.dataIndex;
                const h = top10[idx];
                const lines = [`Share: ${item.raw.toFixed(2)}%`];
                if (h?.exclude_from_concentration) {
                  lines.push('Type: Verified CEX / DEX Reserve');
                } else {
                  lines.push('Type: Individual / Insider Wallet');
                }
                return lines;
              }
            }
          }
        },
        scales: {
          x: {
            min: 0,
            max: Math.max(100, Math.ceil(Math.max(...dataValues, 10) / 10) * 10),
            grid: {
              color: '#F3F4F6',
              drawBorder: false,
            },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: '#9CA3AF',
              callback: (value) => `${value}%`,
            }
          },
          y: {
            grid: {
              display: false,
              drawBorder: false,
            },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: '#6B7280',
            }
          }
        }
      }
    });

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [hasData, top10]);

  return (
    <div className="w-full">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-4 gap-2">
        <div>
          <h3 
            className="text-[18px] font-semibold text-[#0A0A0A]"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Holder distribution
          </h3>
          <p 
            className="text-[13px] text-[#9CA3AF] mt-0.5"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Top 10 wallets by percentage of total supply
          </p>
        </div>

        {hasData && (
          <div className="flex items-center space-x-4 text-[12px] text-[#6B7280]">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-[2px] bg-[#2563EB]" />
              <span>CEX / DEX Reserve</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-[2px] bg-[#0A0A0A]" />
              <span>Individual Wallet</span>
            </div>
          </div>
        )}
      </div>

      {/* Chart Canvas or Placeholder */}
      <div className="w-full h-[280px] bg-white flex items-center justify-center">
        {hasData ? (
          <canvas ref={canvasRef} />
        ) : (
          <div 
            className="text-[13px] text-[#9CA3AF] text-center"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            No data available
          </div>
        )}
      </div>

      {/* Top 10 Holders Detailed Table with Tag Badges */}
      {hasData && (
        <div className="mt-6 border border-[#E5E7EB] rounded-[8px] overflow-hidden">
          <div className="bg-[#FAFAFA] px-4 py-2.5 border-b border-[#E5E7EB] flex items-center justify-between text-[11px] font-medium text-[#6B7280] uppercase tracking-[0.05em]">
            <span>Top 10 Holder Wallets</span>
            <span>Supply Share</span>
          </div>

          <div className="divide-y divide-[#F3F4F6] bg-white">
            {top10.map((h, idx) => {
              const displayAddr = h.owner || h.address;
              const isCex = h.category === 'CEX';
              const isDex = h.category === 'DEX';
              const isKnown = Boolean(h.label);

              return (
                <div key={idx} className="px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-[#FAFAFA] transition-colors">
                  <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
                    <span className="font-mono text-[12px] text-[#9CA3AF] w-5">
                      #{idx + 1}
                    </span>

                    <div className="flex items-center space-x-1.5">
                      <a
                        href={`https://solscan.io/account/${displayAddr}`}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-[13px] font-medium text-[#0A0A0A] hover:underline inline-flex items-center space-x-1"
                        title={displayAddr}
                      >
                        <span>{truncateAddress(displayAddr, 5)}</span>
                        <ExternalLink size={11} className="text-[#9CA3AF]" />
                      </a>

                      <button
                        onClick={() => copyAddress(displayAddr, idx)}
                        className="text-[#9CA3AF] hover:text-[#0A0A0A] p-0.5 cursor-pointer"
                        title="Copy address"
                      >
                        {copiedIdx === idx ? <Check size={11} className="text-[#059669]" /> : <Copy size={11} />}
                      </button>
                    </div>

                    {/* Tag Badge next to wallet */}
                    {isKnown ? (
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-[4px] text-[11px] font-medium border ${
                          isCex
                            ? 'bg-[#EFF6FF] text-[#1D4ED8] border-[#DBEAFE]'
                            : isDex
                            ? 'bg-[#F0FDF4] text-[#15803D] border-[#DCFCE7]'
                            : 'bg-[#F3F4F6] text-[#374151] border-[#E5E7EB]'
                        }`}
                      >
                        {h.label} {isCex ? '· CEX' : isDex ? '· DEX Pool' : ''}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-[4px] text-[11px] font-medium bg-[#F9FAFB] text-[#6B7280] border border-[#E5E7EB]">
                        Individual Wallet
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-3 self-end sm:self-auto">
                    <div className="w-20 hidden md:block h-1.5 bg-[#F3F4F6] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(100, (h.percentage || 0) * 2.5)}%`,
                          backgroundColor: h.exclude_from_concentration ? '#2563EB' : '#0A0A0A'
                        }}
                      />
                    </div>
                    <span className="font-mono text-[13px] font-semibold text-[#0A0A0A] w-14 text-right">
                      {Number(h.percentage || 0).toFixed(2)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
