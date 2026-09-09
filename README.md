# TokenScope — Solana Token Due Diligence Platform

TokenScope is a high-speed, institutional-grade Solana token due diligence platform. Users paste any Solana token mint address and receive a full risk audit report across 6 pillars in seconds, accompanied by a Google Gemini-powered plain-English risk summary and a unique, shareable public URL.

---

## Tech Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: Python + FastAPI + Uvicorn
- **Database**: Supabase (PostgreSQL) with automatic zero-configuration SQLite fallback
- **Onchain Data**: Ankr Public Solana RPC (`https://rpc.ankr.com/solana`)
- **Market Data**: Jupiter API v2 + BirdEye API + DexScreener
- **AI Summary**: Google Gemini API (`gemini-2.0-flash` via `google-generativeai`)
- **Frontend Deploy**: Vercel
- **Backend Deploy**: Railway
- **HTTP Client**: `httpx` (async)

---

## Design System — Strictly White and Black Theme
- **Dominant Tone**: Pure white background (`#FFFFFF`, >80% coverage)
- **Text**: Near-black (`#0A0A0A`)
- **Accents**: Pure black (`#000000`) for emphasis, borders, and badges
- **Cards**: White background with 1px `#E0E0E0` border and subtle box-shadow
- **Risk Badges**:
  - `SAFE`: White background, black text, black border
  - `CAUTION`: Black background, white text
  - `HIGH RISK`: Black background, white text, bold
  - `LIKELY RUG`: Solid black background, white text, bold, slightly larger
- **Typography**: Inter for body text, Space Mono for scores, addresses, and data metrics
- **Geometry**: Sharp square corners (`rounded-none`, 0px border-radius) everywhere

---

## 6 Risk Pillars & Weighting

| Pillar | Weight | Key Checks |
|---|---|---|
| **1. Security** | 35% | Mint authority revocation, freeze authority revocation, LP lock/burn |
| **2. Holder Distribution** | 25% | Top 10 wallet concentration, single largest holder dominance |
| **3. Market Health** | 15% | Liquidity USD depth, 24h trading volume, price stability |
| **4. Contract Intelligence** | 10% | SPL Token vs Token-2022 standard, metadata mutability |
| **5. Social Validity** | 15% | Official website, Twitter/X profile, Telegram community |
| **6. AI Risk Summary** | Synthesis | Plain-English retail investor synthesis generated via Gemini 2.0 Flash |

### Security Auto-Rules:
- **Mint authority enabled**: Automatic score cap of 30/100, CRITICAL flag added.
- **LP unlocked**: CRITICAL flag added.
- **Both above triggered**: Verdict forced to `HIGH RISK` minimum (or `LIKELY RUG` if score < 25).

---

## Environment Variables

### Backend (`backend/.env`)
```env
SOLANA_RPC_URL=https://rpc.ankr.com/solana
BIRDEYE_API_KEY=your_birdeye_api_key
GEMINI_API_KEY=your_google_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_BASE_URL=http://localhost:8000
PORT=8000
```

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

> **Note**: If external API keys are omitted in development mode, TokenScope runs smoothly with its built-in public RPC integrations, synthetic market calculators, and heuristic risk synthesizers.

---

## Quick Start (Local Development)

### 1. Run Backend (FastAPI)
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

### 2. Run Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## API Endpoints

- `POST /api/v1/audit` — accepts `{ "mint_address": "..." }`, runs full parallel audit via `asyncio.gather()`, returns `report_id`.
- `GET /api/v1/report/{report_id}` — returns full report JSON (public, no auth required).
- `GET /api/v1/token/{mint_address}` — returns cached report if audited within the last 15 minutes.
- `GET /api/v1/health` — returns API health status.

---

## Deployment

### Frontend (Vercel)
Connect your GitHub repository to Vercel with Root Directory set to `frontend/`. All SPA client-side routes (`/`, `/loading/:id`, `/report/:id`) are routed to `index.html` via `vercel.json`.

### Backend (Railway)
Connect your repository to Railway with Root Directory set to `backend/`. Railway will automatically build via `railway.json` and start the service with Uvicorn. Set `GEMINI_API_KEY`, `SOLANA_RPC_URL`, and `SUPABASE_URL` in your Railway project variables.
