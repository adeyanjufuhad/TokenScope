import uuid
import re
import asyncio
import httpx
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, status

from models.report import AuditRequest, AuditInitiateResponse, ReportResponse
from services.onchain import get_full_onchain_data
from services.market import fetch_market_data
from services.social import fetch_social_data
from services.scoring import calculate_pillar_scores
from services.ai_summary import generate_ai_summary
from services.asset_registry import get_asset_classification
from db.supabase import get_cached_report, save_report, get_report_by_id

router = APIRouter(prefix="/api/v1", tags=["audit"])

# In-memory registry for in-flight audits
in_flight_audits: Dict[str, Dict[str, Any]] = {}

# Solana Base58 regex pattern (32 to 44 characters)
BASE58_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

async def execute_full_audit(report_id: str, mint_address: str):
    in_flight_audits[report_id] = {
        "status": "processing",
        "mint_address": mint_address,
        "started_at": datetime.now(timezone.utc).isoformat()
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # 1. Parallel execution of onchain, market, and social data
            onchain_res, market_res, social_res = await asyncio.gather(
                get_full_onchain_data(mint_address),
                fetch_market_data(mint_address, client),
                fetch_social_data(mint_address, client),
                return_exceptions=True
            )

            if isinstance(onchain_res, dict) and not isinstance(onchain_res, Exception):
                mint_info = onchain_res.get("mint_info") or {}
                holders = onchain_res.get("holders") or []
                total_supply = onchain_res.get("total_supply") or 0
                mint_auth_enabled = mint_info.get("mint_authority_enabled", False)
                freeze_auth_enabled = mint_info.get("freeze_authority_enabled", False)

                onchain_data = {
                    "available": True,
                    "mint_info": mint_info,
                    "holders": holders,
                    "top_holders": holders,
                    "mint_authority_revoked": not mint_auth_enabled,
                    "freeze_authority_revoked": not freeze_auth_enabled,
                    "supply": total_supply,
                    "decimals": mint_info.get("decimals", 9),
                    "token_program": "SPL Token",
                    "is_metadata_mutable": False
                }
            else:
                onchain_data = {
                    "available": False,
                    "mint_info": {},
                    "holders": [],
                    "top_holders": [],
                    "mint_authority_revoked": True,
                    "freeze_authority_revoked": True,
                    "supply": 0,
                    "token_program": "SPL Token",
                    "is_metadata_mutable": False
                }

            market_data = market_res if not isinstance(market_res, Exception) else {
                "available": False, "liquidity_usd": 0.0, "volume_24h": 0.0,
                "price_usd": 0.0, "price_history": [], "lp_unlocked": False,
                "token_name": None, "token_symbol": None, "market_cap_usd": 0.0, "holder_count": None
            }
            social_data = social_res if not isinstance(social_res, Exception) else {
                "available": False, "website": None, "twitter": None, "telegram": None
            }

            # 1b. Asset classification pre-processor
            asset_meta = get_asset_classification(mint_address)

            # 2. Compute 6-pillar scores and contextual auto-rules
            pillars, overall_score, calc_verdict = calculate_pillar_scores(
                onchain_data, market_data, social_data, asset_meta=asset_meta
            )

            # 3. Generate plain-English AI Summary using Gemini API
            ai_summary_text, ai_verdict = await generate_ai_summary(pillars)

            # Reconcile verdict if Gemini provided one, preserving critical auto-rules
            final_verdict = calc_verdict
            if calc_verdict in ["HIGH RISK", "LIKELY RUG"]:
                final_verdict = calc_verdict  # Never downgrade a critical risk auto-rule
            elif ai_verdict in ["SAFE", "CAUTION", "HIGH RISK", "LIKELY RUG"]:
                final_verdict = ai_verdict

            token_name = asset_meta.get("canonical_name") or market_data.get("token_name") or onchain_data.get("token_name") or "Solana Token"
            raw_symbol = asset_meta.get("canonical_symbol") or market_data.get("token_symbol") or onchain_data.get("token_symbol") or "SOL"
            token_symbol = str(raw_symbol).lstrip("$")

            report_data = {
                "report_id": report_id,
                "mint_address": mint_address,
                "token_name": token_name,
                "token_symbol": token_symbol,
                "asset_classification": asset_meta.get("asset_type", "STANDARD_SPL"),
                "issuer": asset_meta.get("issuer"),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "overall_score": overall_score,
                "verdict": final_verdict,
                "pillars": pillars,
                "ai_summary": ai_summary_text,
                "shareable_url": f"/report/{report_id}"
            }

            # 4. Persist in database
            await save_report(report_data)

            in_flight_audits[report_id] = {
                "status": "completed",
                "report": report_data
            }
        except Exception as e:
            print(f"Error executing audit for {mint_address}: {e}")
            in_flight_audits[report_id] = {
                "status": "failed",
                "error": str(e)
            }

@router.post("/audit", response_model=AuditInitiateResponse)
async def create_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    mint = request.mint_address.strip()
    if not mint or not BASE58_PATTERN.match(mint):
        raise HTTPException(
            status_code=400, 
            detail="Invalid Solana mint address: must be 32 to 44 base58 characters (no spaces or 0/O/I/l)."
        )

    # 1. Check 15-minute cache
    cached = await get_cached_report(mint, max_age_minutes=15)
    if cached:
        return AuditInitiateResponse(
            report_id=cached["report_id"],
            mint_address=mint,
            status="completed",
            message="Loaded from 15-minute audit cache",
            cached=True
        )

    # 2. Initiate fresh audit
    report_id = str(uuid.uuid4())
    in_flight_audits[report_id] = {
        "status": "processing",
        "mint_address": mint
    }
    background_tasks.add_task(execute_full_audit, report_id, mint)

    return AuditInitiateResponse(
        report_id=report_id,
        mint_address=mint,
        status="processing",
        message="Audit initiated in background",
        cached=False
    )
