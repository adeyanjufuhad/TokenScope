from fastapi import APIRouter, HTTPException, Response, status
from typing import Dict, Any
from datetime import datetime, timezone
from db.supabase import get_report_by_id, get_cached_report
from routers.audit import in_flight_audits

router = APIRouter(prefix="/api/v1", tags=["reports"])

@router.get("/report/{report_id}")
async def get_report(report_id: str, response: Response):
    # 1. Check if currently in-flight
    in_flight = in_flight_audits.get(report_id)
    if in_flight:
        status_str = in_flight.get("status")
        if status_str == "processing":
            response.status_code = status.HTTP_202_ACCEPTED
            return {
                "status": "processing",
                "report_id": report_id,
                "message": "Audit in progress. 6 pillars evaluating..."
            }
        elif status_str == "completed" and "report" in in_flight:
            return in_flight["report"]
        elif status_str == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audit failed: {in_flight.get('error', 'Unknown error')}"
            )

    # 2. Check Database (Supabase / SQLite)
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report

@router.get("/token/{mint_address}")
async def get_token_cache(mint_address: str):
    mint = mint_address.strip()
    cached = await get_cached_report(mint, max_age_minutes=15)
    if not cached:
        raise HTTPException(
            status_code=404, 
            detail="No fresh audit cached in the last 15 minutes for this token."
        )
    return cached

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "TokenScope Backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
