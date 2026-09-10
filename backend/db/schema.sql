-- TokenScope Supabase / PostgreSQL Schema

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mint_address TEXT NOT NULL,
    token_name TEXT NOT NULL,
    token_symbol TEXT NOT NULL,
    overall_score INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    pillar_data JSONB NOT NULL,
    ai_summary TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_mint_address ON reports(mint_address);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

CREATE TABLE IF NOT EXISTS tokens (
    mint_address TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    last_audited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Row-Level Security (RLS) Policies
-- Required for Supabase projects where RLS is enabled by default

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE tokens ENABLE ROW LEVEL SECURITY;

-- Allow public read access on reports and tokens
CREATE POLICY "Allow public read access on reports" ON reports FOR SELECT USING (true);
CREATE POLICY "Allow public read access on tokens" ON tokens FOR SELECT USING (true);

-- Allow backend (anon key) to insert/upsert reports and tokens
CREATE POLICY "Allow public insert access on reports" ON reports FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public insert/update access on tokens" ON tokens FOR ALL USING (true);

