#!/usr/bin/env python3
"""
TokenScope — Comprehensive E2E API Test Suite
==============================================
Tests every public endpoint on the live backend (localhost:8000)
and verifies the Vite dev-server proxy (localhost:5173).

Run:  python backend/tests/test_endpoints_e2e.py
"""

import sys
import time
import json
import asyncio
import traceback
from datetime import datetime

import httpx
import pytest

BASE = "http://localhost:8000"
VITE = "http://localhost:5173"
TIMEOUT = httpx.Timeout(30.0)

@pytest.fixture
async def c():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        yield client

# Tokens
USDC  = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
BONK  = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
WSOL  = "So11111111111111111111111111111111111111112"
INVALID = "not-a-valid-address"
FAKE_UUID = "00000000-0000-0000-0000-000000000000"

PASS = "\u2705"
FAIL = "\u274c"
WARN = "\u26a0\ufe0f"

results = []  # (test_name, passed:bool, notes:str)

def record(name, passed, notes=""):
    results.append((name, passed, notes))
    icon = PASS if passed else FAIL
    print(f"  {icon}  {name}")
    if notes:
        for line in notes.strip().split("\n"):
            print(f"       {line}")

def pretty(obj, maxlen=600):
    """Return compact JSON string, truncated."""
    try:
        s = json.dumps(obj, indent=2, default=str)
    except Exception:
        s = str(obj)
    if len(s) > maxlen:
        s = s[:maxlen] + "\n  ... [truncated]"
    return s


# ═══════════════════════════════════════════════════════════════
#  Individual tests
# ═══════════════════════════════════════════════════════════════

async def test_health_root(c: httpx.AsyncClient):
    """GET /health"""
    r = await c.get(f"{BASE}/health")
    ok = r.status_code == 200 and r.json().get("status") == "healthy"
    record("GET /health", ok,
           f"status={r.status_code}  body={pretty(r.json(), 200)}")

async def test_health_api(c: httpx.AsyncClient):
    """GET /api/v1/health"""
    r = await c.get(f"{BASE}/api/v1/health")
    body = r.json()
    ok = r.status_code == 200 and body.get("status") == "healthy"
    record("GET /api/v1/health", ok,
           f"status={r.status_code}  body={pretty(body, 200)}")

async def test_root(c: httpx.AsyncClient):
    """GET /"""
    r = await c.get(f"{BASE}/")
    body = r.json()
    ok = r.status_code == 200 and "service" in body
    record("GET / (root info)", ok,
           f"status={r.status_code}  body={pretty(body, 200)}")

async def test_vite_proxy(c: httpx.AsyncClient):
    """GET http://localhost:5173/api/v1/health via Vite proxy"""
    try:
        r = await c.get(f"{VITE}/api/v1/health")
        body = r.json()
        ok = r.status_code == 200 and body.get("status") == "healthy"
        record("Vite proxy /api/v1/health", ok,
               f"status={r.status_code}  body={pretty(body, 200)}")
    except Exception as e:
        record("Vite proxy /api/v1/health", False,
               f"EXCEPTION: {e}")


# ──── Audit + poll helper ────────────────────────────────────

async def poll_report(c: httpx.AsyncClient, report_id: str,
                      timeout: float = 35.0, interval: float = 1.5):
    """Poll GET /api/v1/report/{id} until completed / failed / timeout."""
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        r = await c.get(f"{BASE}/api/v1/report/{report_id}")
        last = r
        if r.status_code == 200:
            body = r.json()
            if body.get("status") == "processing":
                await asyncio.sleep(interval)
                continue
            return r  # completed report
        if r.status_code == 202:
            await asyncio.sleep(interval)
            continue
        return r  # error response
    return last  # timeout — return last response


async def run_audit(c: httpx.AsyncClient, label: str, mint: str,
                    expect_status: int = 200,
                    expect_error: bool = False):
    """POST /api/v1/audit + optional polling."""
    r = await c.post(f"{BASE}/api/v1/audit", json={"mint_address": mint})
    body = r.json()

    if expect_error:
        ok = r.status_code == expect_status
        record(f"POST /api/v1/audit [{label}]", ok,
               f"status={r.status_code}  body={pretty(body, 300)}")
        return None

    # Successful initiation
    ok_init = r.status_code == 200 and "report_id" in body
    record(f"POST /api/v1/audit [{label}] initiate", ok_init,
           f"status={r.status_code}  body={pretty(body, 300)}")
    if not ok_init:
        return None

    report_id = body["report_id"]
    is_cached = body.get("cached", False)

    if body.get("status") == "completed" and is_cached:
        # Already cached — fetch full report
        rr = await c.get(f"{BASE}/api/v1/report/{report_id}")
        rr_body = rr.json()
        ok_report = rr.status_code == 200 and "overall_score" in rr_body
        record(f"  ↳ report (cached) [{label}]", ok_report,
               f"status={rr.status_code}  verdict={rr_body.get('verdict')}  "
               f"score={rr_body.get('overall_score')}  "
               f"token={rr_body.get('token_name')}/{rr_body.get('token_symbol')}  "
               f"classification={rr_body.get('asset_classification')}")
        return rr_body

    # Poll until done
    rr = await poll_report(c, report_id)
    if rr is None:
        record(f"  ↳ report poll [{label}]", False, "poll returned None")
        return None
    rr_body = rr.json()
    if rr.status_code == 200 and "overall_score" in rr_body:
        record(f"  ↳ report (fresh) [{label}]", True,
               f"status={rr.status_code}  verdict={rr_body.get('verdict')}  "
               f"score={rr_body.get('overall_score')}  "
               f"token={rr_body.get('token_name')}/{rr_body.get('token_symbol')}  "
               f"classification={rr_body.get('asset_classification')}")
        return rr_body
    elif rr.status_code == 202:
        record(f"  ↳ report poll [{label}]", False,
               f"TIMEOUT – still 202 after 35 s.  body={pretty(rr_body, 200)}")
        return None
    else:
        record(f"  ↳ report poll [{label}]", False,
               f"status={rr.status_code}  body={pretty(rr_body, 300)}")
        return None


# ──── Invalid / edge-case audit tests ────────────────────────

async def test_audit_invalid(c: httpx.AsyncClient):
    """POST /api/v1/audit with invalid address"""
    await run_audit(c, "INVALID ADDRESS", INVALID,
                    expect_status=400, expect_error=True)

async def test_audit_empty_body(c: httpx.AsyncClient):
    """POST /api/v1/audit with empty JSON body {}"""
    r = await c.post(f"{BASE}/api/v1/audit", json={})
    ok = r.status_code == 422  # Pydantic validation error expected
    record("POST /api/v1/audit [empty body {}]", ok,
           f"status={r.status_code}  body={pretty(r.json(), 300)}")

async def test_audit_no_body(c: httpx.AsyncClient):
    """POST /api/v1/audit with no body at all"""
    r = await c.post(f"{BASE}/api/v1/audit")
    ok = r.status_code == 422
    record("POST /api/v1/audit [no body]", ok,
           f"status={r.status_code}  body={pretty(r.json(), 300)}")


# ──── Report not-found ────────────────────────────────────────

async def test_report_not_found(c: httpx.AsyncClient):
    """GET /api/v1/report/{fake-uuid}"""
    r = await c.get(f"{BASE}/api/v1/report/{FAKE_UUID}")
    ok = r.status_code == 404
    record("GET /api/v1/report/{fake-uuid}", ok,
           f"status={r.status_code}  body={pretty(r.json(), 200)}")


# ──── Token cache lookup ─────────────────────────────────────

async def test_token_cached(c: httpx.AsyncClient, mint: str, label: str):
    """GET /api/v1/token/{mint}"""
    r = await c.get(f"{BASE}/api/v1/token/{mint}")
    body = r.json()
    # Could be 200 (cached) or 404 (no cache), both are valid
    if r.status_code == 200:
        record(f"GET /api/v1/token/{label}", True,
               f"status=200  verdict={body.get('verdict')}  score={body.get('overall_score')}")
    elif r.status_code == 404:
        record(f"GET /api/v1/token/{label}", True,
               f"status=404 (no fresh cache) — expected if token not recently audited")
    else:
        record(f"GET /api/v1/token/{label}", False,
               f"status={r.status_code}  body={pretty(body, 200)}")


# ──── Watchlist ───────────────────────────────────────────────

async def test_watchlist_get(c: httpx.AsyncClient):
    """GET /api/v1/watchlist"""
    r = await c.get(f"{BASE}/api/v1/watchlist")
    body = r.json()
    ok = r.status_code == 200 and "watchlist" in body
    wl = body.get("watchlist", [])
    record("GET /api/v1/watchlist", ok,
           f"status={r.status_code}  items={len(wl)}  body={pretty(body, 400)}")

async def test_watchlist_post(c: httpx.AsyncClient):
    """POST /api/v1/watchlist (not implemented → expect 405)"""
    r = await c.post(f"{BASE}/api/v1/watchlist",
                     json={"mint_address": USDC, "name": "USDC", "symbol": "USDC"})
    if r.status_code == 405:
        record("POST /api/v1/watchlist", True,
               f"status=405 — Method Not Allowed (no POST route defined)")
    elif r.status_code == 200 or r.status_code == 201:
        record("POST /api/v1/watchlist", True,
               f"status={r.status_code} — POST route exists  body={pretty(r.json(), 200)}")
    else:
        record("POST /api/v1/watchlist", False,
               f"status={r.status_code}  body={pretty(r.json() if r.headers.get('content-type','').startswith('application/json') else r.text[:200], 200)}")

async def test_watchlist_delete(c: httpx.AsyncClient):
    """DELETE /api/v1/watchlist/{mint} (not implemented → expect 405)"""
    r = await c.delete(f"{BASE}/api/v1/watchlist/{USDC}")
    if r.status_code == 405:
        record("DELETE /api/v1/watchlist/{mint}", True,
               f"status=405 — Method Not Allowed (no DELETE route defined)")
    elif r.status_code == 200 or r.status_code == 204:
        record("DELETE /api/v1/watchlist/{mint}", True,
               f"status={r.status_code} — DELETE route exists")
    else:
        record("DELETE /api/v1/watchlist/{mint}", False,
               f"status={r.status_code}  Unexpected response")


# ──── OpenAPI docs ────────────────────────────────────────────

async def test_openapi_docs(c: httpx.AsyncClient):
    """GET /docs  and  GET /openapi.json"""
    r_docs = await c.get(f"{BASE}/docs")
    ok_docs = r_docs.status_code == 200
    record("GET /docs (Swagger UI)", ok_docs,
           f"status={r_docs.status_code}  content-type={r_docs.headers.get('content-type','?')}")

    r_schema = await c.get(f"{BASE}/openapi.json")
    ok_schema = r_schema.status_code == 200
    if ok_schema:
        paths = list(r_schema.json().get("paths", {}).keys())
        record("GET /openapi.json", True,
               f"status=200  registered_paths={paths}")
    else:
        record("GET /openapi.json", False,
               f"status={r_schema.status_code}")


# ═══════════════════════════════════════════════════════════════
#  Main runner
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 72)
    print("  TokenScope E2E API Test Suite")
    print(f"  Started: {datetime.now().isoformat()}")
    print(f"  Backend: {BASE}   Vite: {VITE}")
    print("=" * 72)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:

        # ── 1. Health & root ──────────────────────────────────
        print("\n[1/8] Health & Root Endpoints")
        await test_health_root(c)
        await test_health_api(c)
        await test_root(c)

        # ── 2. Vite proxy ────────────────────────────────────
        print("\n[2/8] Vite Dev-Server Proxy")
        await test_vite_proxy(c)

        # ── 3. Invalid / edge-case audits ─────────────────────
        print("\n[3/8] Audit Edge Cases (invalid input)")
        await test_audit_invalid(c)
        await test_audit_empty_body(c)
        await test_audit_no_body(c)

        # ── 4. Real audits (sequential to avoid rate limits) ─
        print("\n[4/8] Audit: USDC")
        usdc_report = await run_audit(c, "USDC", USDC)

        print("\n[5/8] Audit: BONK")
        bonk_report = await run_audit(c, "BONK", BONK)

        print("\n[6/8] Audit: WSOL")
        wsol_report = await run_audit(c, "WSOL", WSOL)

        # ── 5. Report not-found ──────────────────────────────
        print("\n[7/8] Report & Token Cache")
        await test_report_not_found(c)

        # Token cache lookup for USDC (should exist if audit ran)
        await test_token_cached(c, USDC, "USDC")
        await test_token_cached(c, BONK, "BONK")

        # ── 6. Watchlist ─────────────────────────────────────
        print("\n[8/8] Watchlist & Misc")
        await test_watchlist_get(c)
        await test_watchlist_post(c)
        await test_watchlist_delete(c)
        await test_openapi_docs(c)

    # ── Summary ──────────────────────────────────────────────
    print("\n" + "=" * 72)
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed
    print(f"  RESULTS:  {passed}/{total} passed   |   {failed} failed")
    print("=" * 72)

    if failed:
        print(f"\n  {FAIL}  FAILED TESTS:")
        for name, ok, notes in results:
            if not ok:
                print(f"     • {name}")
                if notes:
                    for line in notes.strip().split("\n"):
                        print(f"       {line}")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        rc = asyncio.run(main())
    except Exception as e:
        print(f"\n{FAIL} FATAL: {e}")
        traceback.print_exc()
        rc = 2
    sys.exit(rc)
