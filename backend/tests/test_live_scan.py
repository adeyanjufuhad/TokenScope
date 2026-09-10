import httpx
import time
import sqlite3
from pathlib import Path

BASE_BACKEND = "http://127.0.0.1:8000"
BASE_VITE_PROXY = "http://localhost:5173"

def run_tests():
    results = []
    
    with httpx.Client(timeout=45.0) as client:
        # Test 1: GET /
        try:
            r = client.get(f"{BASE_BACKEND}/")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            results.append(("GET /", "PASS", r.json()))
        except Exception as e:
            results.append(("GET /", "FAIL", str(e)))

        # Test 2: GET /health
        try:
            r = client.get(f"{BASE_BACKEND}/health")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert r.json().get("status") == "healthy"
            results.append(("GET /health", "PASS", r.json()))
        except Exception as e:
            results.append(("GET /health", "FAIL", str(e)))

        # Test 3: GET /api/v1/health
        try:
            r = client.get(f"{BASE_BACKEND}/api/v1/health")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert r.json().get("status") == "healthy"
            results.append(("GET /api/v1/health", "PASS", r.json()))
        except Exception as e:
            results.append(("GET /api/v1/health", "FAIL", str(e)))

        # Test 4: Vite Proxy to /api/v1/health
        try:
            r = client.get(f"{BASE_VITE_PROXY}/api/v1/health")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            results.append(("Vite Proxy GET /api/v1/health", "PASS", r.json()))
        except Exception as e:
            results.append(("Vite Proxy GET /api/v1/health", "FAIL", str(e)))

        # Test 5: POST /api/v1/audit with empty body
        try:
            r = client.post(f"{BASE_BACKEND}/api/v1/audit", json={})
            assert r.status_code == 422, f"Expected 422, got {r.status_code}"
            results.append(("POST /audit empty body (422)", "PASS", "Rejected with 422 Unprocessable Entity"))
        except Exception as e:
            results.append(("POST /audit empty body (422)", "FAIL", str(e)))

        # Test 6: POST /api/v1/audit with invalid address
        try:
            r = client.post(f"{BASE_BACKEND}/api/v1/audit", json={"mint_address": "not-a-valid-solana-address"})
            assert r.status_code == 400, f"Expected 400, got {r.status_code}"
            results.append(("POST /audit invalid base58 (400)", "PASS", r.json().get("detail")))
        except Exception as e:
            results.append(("POST /audit invalid base58 (400)", "FAIL", str(e)))

        # Test 7: GET /api/v1/report with non-existent UUID
        try:
            r = client.get(f"{BASE_BACKEND}/api/v1/report/00000000-0000-0000-0000-000000000000")
            assert r.status_code == 404, f"Expected 404, got {r.status_code}"
            results.append(("GET /report non-existent (404)", "PASS", r.json().get("detail")))
        except Exception as e:
            results.append(("GET /report non-existent (404)", "FAIL", str(e)))

        # Test 8: GET /api/v1/watchlist
        try:
            r = client.get(f"{BASE_BACKEND}/api/v1/watchlist")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            watchlist = r.json().get("watchlist", [])
            assert len(watchlist) > 0, "Watchlist should not be empty"
            results.append(("GET /watchlist", "PASS", f"{len(watchlist)} tokens in watchlist"))
        except Exception as e:
            results.append(("GET /watchlist", "FAIL", str(e)))

        # Test 9: Full Audit of Canonical USDC
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        try:
            r = client.post(f"{BASE_BACKEND}/api/v1/audit", json={"mint_address": usdc_mint})
            assert r.status_code == 200
            init_data = r.json()
            report_id = init_data["report_id"]
            
            # Poll report
            report = None
            for _ in range(20):
                time.sleep(1.5)
                rr = client.get(f"{BASE_BACKEND}/api/v1/report/{report_id}")
                if rr.status_code == 200:
                    report = rr.json()
                    break
            
            assert report is not None, "Report did not complete in 30s"
            assert report.get("overall_score") >= 90, f"USDC score {report.get('overall_score')} < 90"
            assert report.get("asset_classification") == "STABLECOIN"
            assert report.get("token_symbol") == "USDC"
            results.append(("USDC Full Audit", "PASS", {
                "score": report.get("overall_score"),
                "verdict": report.get("verdict"),
                "classification": report.get("asset_classification"),
                "issuer": report.get("issuer"),
                "symbol": report.get("token_symbol")
            }))
        except Exception as e:
            results.append(("USDC Full Audit", "FAIL", str(e)))

        # Test 10: GET /api/v1/token/{mint} cache lookup
        try:
            r = client.get(f"{BASE_BACKEND}/api/v1/token/{usdc_mint}")
            assert r.status_code == 200, f"Expected 200, got {r.status_code}"
            assert r.json().get("token_symbol") == "USDC"
            results.append(("GET /token/{mint} cache hit", "PASS", f"Cached report retrieved: {r.json().get('report_id')}"))
        except Exception as e:
            results.append(("GET /token/{mint} cache hit", "FAIL", str(e)))

        # Test 11: Full Audit of BONK (Standard Memecoin)
        bonk_mint = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
        try:
            r = client.post(f"{BASE_BACKEND}/api/v1/audit", json={"mint_address": bonk_mint})
            assert r.status_code == 200
            report_id = r.json()["report_id"]
            
            report = None
            for _ in range(20):
                time.sleep(1.5)
                rr = client.get(f"{BASE_BACKEND}/api/v1/report/{report_id}")
                if rr.status_code == 200:
                    report = rr.json()
                    break
            
            assert report is not None, "BONK report did not complete"
            holders = report.get("pillars", {}).get("holders", {}).get("top_holders", [])
            known_tagged = [h for h in holders if h.get("is_known_entity")]
            results.append(("BONK Memecoin Audit", "PASS", {
                "score": report.get("overall_score"),
                "verdict": report.get("verdict"),
                "classification": report.get("asset_classification"),
                "symbol": report.get("token_symbol"),
                "known_entities_detected": len(known_tagged)
            }))
        except Exception as e:
            results.append(("BONK Memecoin Audit", "FAIL", str(e)))

        # Test 12: Full Audit of WSOL (Canonical Wrapped)
        wsol_mint = "So11111111111111111111111111111111111111112"
        try:
            r = client.post(f"{BASE_BACKEND}/api/v1/audit", json={"mint_address": wsol_mint})
            assert r.status_code == 200
            report_id = r.json()["report_id"]
            
            report = None
            for _ in range(20):
                time.sleep(1.5)
                rr = client.get(f"{BASE_BACKEND}/api/v1/report/{report_id}")
                if rr.status_code == 200:
                    report = rr.json()
                    break
            
            assert report is not None, "WSOL report did not complete"
            results.append(("WSOL Wrapped Audit", "PASS", {
                "score": report.get("overall_score"),
                "verdict": report.get("verdict"),
                "classification": report.get("asset_classification"),
                "symbol": report.get("token_symbol")
            }))
        except Exception as e:
            results.append(("WSOL Wrapped Audit", "FAIL", str(e)))

        # Test 13: Local SQLite Database Inspection
        try:
            db_path = Path(__file__).parent.parent / "tokenscope.db"
            assert db_path.exists(), f"Database file {db_path} does not exist"
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM reports;")
                count = cursor.fetchone()[0]
                assert count > 0, "No reports persisted in SQLite"
                cursor.execute("SELECT mint_address, token_symbol, overall_score FROM reports ORDER BY created_at DESC LIMIT 3;")
                recent = cursor.fetchall()
            results.append(("SQLite Persistence Check", "PASS", {
                "total_reports": count,
                "recent_saved": recent
            }))
        except Exception as e:
            results.append(("SQLite Persistence Check", "FAIL", str(e)))

    print("\n" + "="*70)
    print("           TOKENSCOPE COMPREHENSIVE SCAN RESULTS")
    print("="*70)
    all_passed = True
    for name, status, details in results:
        flag = "[PASS]" if status == "PASS" else "[FAIL]"
        if status != "PASS":
            all_passed = False
        print(f"{flag} {name:<35} : {details}")
    print("="*70)
    print(f"OVERALL STATUS: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}\n")

if __name__ == "__main__":
    run_tests()
