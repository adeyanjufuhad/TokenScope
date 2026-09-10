import React, { useEffect, useRef } from 'react';
import { Chart as ChartJS } from 'chart.js/auto';

export default function PriceSparkline({ prices = [] }) {
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);

  const validPrices = (prices || []).filter(p => typeof p === 'number' && !isNaN(p) && p >= 0);
  const hasData = validPrices.length > 0;

  useEffect(() => {
    if (!hasData || !canvasRef.current) return;

    const Chart = ChartJS || window.Chart;
    if (!Chart) return;

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
      chartInstanceRef.current = null;
    }

    // Generate day labels e.g. Day 1, Day 2 ...
    const labels = validPrices.map((_, idx) => {
      const dayOffset = validPrices.length - 1 - idx;
      if (dayOffset === 0) return 'Today';
      return `${dayOffset}d ago`;
    });

    const formatPrice = (val) => {
      if (val === null || val === undefined) return '$0.00';
      if (val < 0.0001 && val > 0) return `$${val.toExponential(4)}`;
      if (val < 1) return `$${val.toFixed(6)}`;
      return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`;
    };

    const ctx = canvasRef.current.getContext('2d');
    chartInstanceRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            data: validPrices,
            borderColor: '#0A0A0A',
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#0A0A0A',
            pointBorderColor: '#FFFFFF',
            pointBorderWidth: 1.5,
            tension: 0.3,
            fill: false,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: '#0A0A0A',
            titleColor: '#9CA3AF',
            bodyColor: '#FFFFFF',
            titleFont: { family: 'Inter', size: 11 },
            bodyFont: { family: 'IBM Plex Mono', size: 12, weight: '600' },
            padding: 10,
            cornerRadius: 6,
            displayColors: false,
            callbacks: {
              label: (item) => formatPrice(item.raw)
            }
          }
        },
        scales: {
          x: {
            grid: {
              color: '#F3F4F6',
              drawBorder: false,
            },
            ticks: {
              font: { family: 'Inter', size: 11 },
              color: '#9CA3AF',
            }
          },
          y: {
            grid: {
              color: '#F3F4F6',
              drawBorder: false,
            },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: '#9CA3AF',
              callback: (value) => formatPrice(value),
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
  }, [hasData, validPrices]);

  return (
    <div className="w-full">
      {/* Section Header */}
      <div className="mb-4">
        <h3 
          className="text-[18px] font-semibold text-[#0A0A0A]"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Price history (7 days)
        </h3>
        <p 
          className="text-[13px] text-[#9CA3AF] mt-0.5"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Closing price per day in USD
        </p>
      </div>

      {/* Line Chart Canvas or Placeholder */}
      <div className="w-full h-[200px] bg-white flex items-center justify-center">
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
    </div>
  );
}
