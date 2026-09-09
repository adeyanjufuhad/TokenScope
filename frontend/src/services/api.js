const CUSTOM_API_URL = import.meta.env.VITE_API_BASE_URL;

export function truncateAddress(address, chars = 4) {
  if (!address) return '';
  if (address.length <= chars * 2 + 3) return address;
  return `${address.slice(0, chars)}...${address.slice(-chars)}`;
}

/**
 * Resilient fetcher:
 * 1. Uses VITE_API_BASE_URL if configured.
 * 2. Defaults to relative path (handled by Vite dev proxy or production reverse proxy).
 * 3. Falls back to direct http://localhost:8000 if relative request cannot connect.
 * 4. Yields descriptive error if backend is stopped.
 */
async function apiFetch(endpoint, options = {}) {
  if (CUSTOM_API_URL) {
    try {
      return await fetch(`${CUSTOM_API_URL}${endpoint}`, options);
    } catch (err) {
      throw new Error(`Unable to connect to backend at ${CUSTOM_API_URL}. Ensure the server is running.`);
    }
  }

  try {
    return await fetch(endpoint, options);
  } catch (primaryErr) {
    // Relative request failed (e.g. proxy unavailable) -> try direct localhost:8000
    try {
      return await fetch(`http://localhost:8000${endpoint}`, options);
    } catch {
      throw new Error('TokenScope backend is not reachable. Please ensure the backend server is running on port 8000.');
    }
  }
}

export async function auditToken(mintAddress) {
  const res = await apiFetch('/api/v1/audit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ mint_address: mintAddress.trim() }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to initiate audit' }));
    throw new Error(err.detail || 'Audit request failed');
  }

  return res.json();
}

export async function getReport(reportId) {
  const res = await apiFetch(`/api/v1/report/${reportId}`);
  
  if (res.status === 202) {
    return { status: 'processing', report_id: reportId };
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Report not found' }));
    throw new Error(err.detail || 'Failed to fetch report');
  }

  return res.json();
}

export async function getCachedToken(mintAddress) {
  try {
    const res = await apiFetch(`/api/v1/token/${encodeURIComponent(mintAddress.trim())}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function checkHealth() {
  try {
    const res = await apiFetch('/api/v1/health');
    return res.ok;
  } catch {
    return false;
  }
}
