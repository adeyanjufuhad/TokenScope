import React, { useState } from 'react';
import { Share2, Check } from 'lucide-react';

export default function ShareButton() {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy shareable link:', err);
    }
  };

  return (
    <button
      onClick={handleShare}
      className="inline-flex items-center space-x-1.5 px-4 py-1.5 bg-[#0A0A0A] hover:bg-[#1F2937] text-white text-[13px] font-medium rounded-[6px] transition-colors cursor-pointer select-none"
      style={{ fontFamily: 'Inter, sans-serif' }}
    >
      {copied ? (
        <>
          <Check size={14} />
          <span>Copied!</span>
        </>
      ) : (
        <>
          <Share2 size={13} />
          <span>Share report</span>
        </>
      )}
    </button>
  );
}
