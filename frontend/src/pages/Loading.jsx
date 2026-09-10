import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Check } from 'lucide-react';
import { getReport, truncateAddress } from '../services/api';

const PILLARS = [
  { name: 'Security checks', time: '0.8s' },
  { name: 'Holder distribution', time: '1.2s' },
  { name: 'Market health', time: '1.1s' },
  { name: 'Contract intelligence', time: '0.9s' },
  { name: 'Social validity', time: '1.4s' },
  { name: 'AI risk synthesis', time: '1.6s' },
];

export default function Loading() {
  const { report_id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const mintAddress = location.state?.mintAddress || '';

  const [currentStep, setCurrentStep] = useState(0);
  const [pollError, setPollError] = useState(null);
  const pollTimerRef = useRef(null);
  const pollAttemptsRef = useRef(0);

  // Progressive checklist animation across the 6 pillars
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < PILLARS.length - 1) return prev + 1;
        return prev;
      });
    }, 1100);

    return () => clearInterval(timer);
  }, []);

  // Poll GET /api/v1/report/{report_id} every 2 seconds (with 40s timeout)
  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      pollAttemptsRef.current += 1;
      
      // Safety timeout after 25 attempts (~50s)
      if (pollAttemptsRef.current > 25) {
        if (isMounted) {
          setPollError('Audit timed out. Solana RPC or market APIs took too long to respond.');
        }
        return;
      }

      try {
        const report = await getReport(report_id);
        if (!isMounted) return;

        if (report && report.status === 'failed') {
          setPollError(report.message || 'Audit failed to complete. Please check the token address and try again.');
          return;
        }

        if (report && report.status !== 'processing' && report.report_id) {
          setCurrentStep(PILLARS.length);
          setTimeout(() => {
            if (isMounted) {
              navigate(`/report/${report_id}`, { replace: true });
            }
          }, 350);
        } else {
          pollTimerRef.current = setTimeout(poll, 2000);
        }
      } catch (err) {
        if (!isMounted) return;
        // If report is 404 or failed on server
        if (pollAttemptsRef.current > 5 && err.message?.includes('not found')) {
          setPollError('Audit report was not found. Please initiate a new audit.');
          return;
        }
        pollTimerRef.current = setTimeout(poll, 2000);
      }
    };

    pollTimerRef.current = setTimeout(poll, 1200);

    return () => {
      isMounted = false;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [report_id, navigate]);

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col justify-between relative">
      {/* Top 2px Animated Progress Bar (0% to 95% over 8s) */}
      <div className="w-full h-[2px] bg-[#F3F4F6] fixed top-0 left-0 z-50 overflow-hidden">
        <div className="h-full bg-[#0A0A0A] animate-loading-bar" />
      </div>

      {/* Main Centered Content */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-[480px] bg-white border border-[#E5E7EB] rounded-[12px] p-8 sm:p-10 shadow-card">
          
          {/* a) Truncated Address pill */}
          {mintAddress && (
            <div className="inline-block bg-[#F9FAFB] border border-[#E5E7EB] rounded-[6px] px-3 py-1.5 font-mono text-[13px] text-[#0A0A0A]">
              {truncateAddress(mintAddress, 8)}
            </div>
          )}

          {/* b) Heading */}
          <h2 
            className="text-[20px] font-semibold text-[#0A0A0A] mt-5"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {pollError ? 'Unable to complete audit' : 'Auditing token'}
          </h2>

          {/* c) Subheading or Error UI */}
          {pollError ? (
            <div className="mt-3">
              <p className="text-[14px] text-[#DC2626] bg-[#FEF2F2] border border-[#FEE2E2] p-3 rounded-[8px] mb-5">
                {pollError}
              </p>
              <button
                onClick={() => navigate('/')}
                className="w-full py-2.5 bg-[#0A0A0A] hover:bg-[#1F2937] text-white text-[13px] font-medium rounded-[8px] transition-colors cursor-pointer"
              >
                ← Return to audit terminal
              </button>
            </div>
          ) : (
            <>
              <p 
                className="text-[14px] text-[#6B7280] mt-1"
                style={{ fontFamily: 'Inter, sans-serif' }}
              >
                Fetching onchain data and running risk analysis...
              </p>

              {/* d) 6 Checklist Items */}
              <div className="mt-6 space-y-3.5">
                {PILLARS.map((pillar, idx) => {
                  const isCompleted = idx < currentStep;
                  const isActive = idx === currentStep;

                  return (
                    <div key={pillar.name} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {/* Circle Indicator (20px) */}
                        {isCompleted ? (
                          <div className="w-5 h-5 rounded-full bg-[#0A0A0A] flex items-center justify-center shrink-0">
                            <Check size={12} strokeWidth={2.5} className="text-white" />
                          </div>
                        ) : isActive ? (
                          <div className="w-5 h-5 rounded-full border-[2px] border-[#0A0A0A] border-t-transparent animate-spin-custom shrink-0" />
                        ) : (
                          <div className="w-5 h-5 rounded-full border-[2px] border-[#E5E7EB] shrink-0" />
                        )}

                        {/* Pillar Name */}
                        <span 
                          className={`text-[14px] font-medium ${
                            isCompleted || isActive ? 'text-[#0A0A0A]' : 'text-[#9CA3AF]'
                          }`}
                          style={{ fontFamily: 'Inter, sans-serif' }}
                        >
                          {pillar.name}
                        </span>
                      </div>

                      {/* Far right: Elapsed Time in IBM Plex Mono 12px */}
                      {isCompleted && (
                        <span className="font-mono text-[12px] text-[#9CA3AF]">
                          {pillar.time}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {/* e) Bottom Divider & Cache note */}
          <div className="mt-8 pt-4 border-t border-[#E5E7EB] text-center">
            <span 
              className="text-[12px] text-[#9CA3AF]"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Reports are cached for 15 minutes
            </span>
          </div>

        </div>
      </div>

      {/* Subtle footer */}
      <footer className="w-full py-4 text-center text-[12px] text-[#9CA3AF]">
        TokenScope Intelligence Pipeline
      </footer>
    </div>
  );
}
