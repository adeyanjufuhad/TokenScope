import os
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()

supabase_client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("Connected to Supabase successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}. Falling back to SQLite.")
        supabase_client = None

# SQLite fallback database file
DB_FILE = Path(__file__).parent.parent / "tokenscope.db"

def init_sqlite():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                mint_address TEXT NOT NULL,
                token_name TEXT NOT NULL,
                token_symbol TEXT NOT NULL,
                overall_score INTEGER NOT NULL,
                verdict TEXT NOT NULL,
                pillar_data TEXT NOT NULL,
                ai_summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mint_created ON reports(mint_address, created_at DESC);")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                mint_address TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                last_audited_at TEXT NOT NULL
            );
        """)
        conn.commit()

init_sqlite()

def _format_report_dict(row: Dict[str, Any], base_url: str = "") -> Dict[str, Any]:
    pillar_data = row.get("pillar_data")
    if isinstance(pillar_data, str):
        try:
            pillar_data = json.loads(pillar_data)
        except Exception:
            pillar_data = {}

    report_id = str(row.get("id"))
    return {
        "report_id": report_id,
        "mint_address": row.get("mint_address"),
        "token_name": row.get("token_name"),
        "token_symbol": row.get("token_symbol"),
        "generated_at": row.get("created_at"),
        "overall_score": int(row.get("overall_score", 0)),
        "verdict": row.get("verdict"),
        "pillars": pillar_data,
        "ai_summary": row.get("ai_summary", ""),
        "shareable_url": f"/report/{report_id}"
    }

async def get_cached_report(mint_address: str, max_age_minutes: int = 15) -> Optional[Dict[str, Any]]:
    cutoff_dt = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    cutoff_iso = cutoff_dt.isoformat()

    # 1. Try Supabase if configured
    if supabase_client:
        try:
            response = supabase_client.table("reports") \
                .select("*") \
                .eq("mint_address", mint_address) \
                .gte("created_at", cutoff_iso) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            if response.data and len(response.data) > 0:
                return _format_report_dict(response.data[0])
        except Exception as e:
            print(f"Supabase query error: {e}, attempting SQLite fallback")

    # 2. SQLite fallback
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reports 
                WHERE mint_address = ? AND created_at >= ?
                ORDER BY created_at DESC 
                LIMIT 1
            """, (mint_address, cutoff_iso))
            row = cursor.fetchone()
            if row:
                return _format_report_dict(dict(row))
    except Exception as e:
        print(f"SQLite query error: {e}")

    return None

async def get_report_by_id(report_id: str) -> Optional[Dict[str, Any]]:
    # 1. Try Supabase
    if supabase_client:
        try:
            response = supabase_client.table("reports") \
                .select("*") \
                .eq("id", report_id) \
                .limit(1) \
                .execute()
            if response.data and len(response.data) > 0:
                return _format_report_dict(response.data[0])
        except Exception as e:
            print(f"Supabase get_report_by_id error: {e}, falling back to SQLite")

    # 2. SQLite fallback
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE id = ? LIMIT 1", (report_id,))
            row = cursor.fetchone()
            if row:
                return _format_report_dict(dict(row))
    except Exception as e:
        print(f"SQLite get_report_by_id error: {e}")

    return None

async def save_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    report_id = report_data.get("report_id")
    mint_address = report_data.get("mint_address")
    token_name = report_data.get("token_name")
    token_symbol = report_data.get("token_symbol")
    overall_score = report_data.get("overall_score")
    verdict = report_data.get("verdict")
    pillar_data = report_data.get("pillars")
    ai_summary = report_data.get("ai_summary")
    created_at = report_data.get("generated_at") or datetime.now(timezone.utc).isoformat()

    pillar_data_json = json.dumps(pillar_data) if isinstance(pillar_data, dict) else str(pillar_data)

    # 1. Save to Supabase if configured
    if supabase_client:
        try:
            row_data = {
                "id": report_id,
                "mint_address": mint_address,
                "token_name": token_name,
                "token_symbol": token_symbol,
                "overall_score": overall_score,
                "verdict": verdict,
                "pillar_data": pillar_data if isinstance(pillar_data, dict) else json.loads(pillar_data_json),
                "ai_summary": ai_summary,
                "created_at": created_at
            }
            supabase_client.table("reports").insert(row_data).execute()
            supabase_client.table("tokens").upsert({
                "mint_address": mint_address,
                "name": token_name,
                "symbol": token_symbol,
                "last_audited_at": created_at
            }).execute()
        except Exception as e:
            print(f"Supabase insert error: {e}, persisting in SQLite")

    # 2. Always persist to SQLite as well for local durability
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO reports 
                (id, mint_address, token_name, token_symbol, overall_score, verdict, pillar_data, ai_summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (report_id, mint_address, token_name, token_symbol, overall_score, verdict, pillar_data_json, ai_summary, created_at))
            
            cursor.execute("""
                INSERT OR REPLACE INTO tokens (mint_address, name, symbol, last_audited_at)
                VALUES (?, ?, ?, ?)
            """, (mint_address, token_name, token_symbol, created_at))
            conn.commit()
    except Exception as e:
        print(f"SQLite save_report error: {e}")

    return report_data
