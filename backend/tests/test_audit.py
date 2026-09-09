import pytest
import asyncio
from services.scoring import calculate_pillar_scores
from services.ai_summary import generate_ai_summary
from db.supabase import save_report, get_report_by_id, get_cached_report

def test_mint_authority_cap_auto_rule():
    onchain_data = {
        "token_name": "Test Token",
        "token_symbol": "TEST",
        "mint_authority_revoked": False,  # Mint enabled!
        "freeze_authority_revoked": True,
        "token_program": "SPL Token",
        "top_holders": [{"address": "Addr1", "percentage": 10.0}]
    }
    market_data = {
        "liquidity_usd": 500000.0,
        "volume_24h": 200000.0,
        "price_usd": 10.0,
        "price_history": [10.0] * 7,
        "lp_unlocked": False
    }
    social_data = {
        "website": "https://example.com",
        "twitter": "https://x.com/example",
        "telegram": "https://t.me/example"
    }

    pillars, overall_score, verdict = calculate_pillar_scores(onchain_data, market_data, social_data)
    
    # Assert mint authority enabled capped the score at 30
    assert overall_score <= 30, f"Expected score <= 30, got {overall_score}"
    # Assert CRITICAL flag exists in security
    critical_flags = [f for f in pillars["security"]["flags"] if f["severity"] == "CRITICAL"]
    assert len(critical_flags) >= 1
    assert "Mint authority is ENABLED" in critical_flags[0]["label"]

def test_both_mint_and_lp_unlocked_forces_high_risk():
    onchain_data = {
        "token_name": "Rug Candidate",
        "token_symbol": "RUG",
        "mint_authority_revoked": False,  # Mint enabled
        "freeze_authority_revoked": False,
        "token_program": "SPL Token",
        "top_holders": [{"address": "Addr1", "percentage": 85.0}]
    }
    market_data = {
        "liquidity_usd": 1000.0,
        "volume_24h": 500.0,
        "price_usd": 0.01,
        "price_history": [0.01] * 7,
        "lp_unlocked": True  # LP unlocked
    }
    social_data = {
        "website": None,
        "twitter": None,
        "telegram": None
    }

    pillars, overall_score, verdict = calculate_pillar_scores(onchain_data, market_data, social_data)
    
    assert verdict in ["HIGH RISK", "LIKELY RUG"]
    assert overall_score <= 30

def test_ai_summary_generation():
    mock_pillars = {
        "security": {"flags": [{"label": "Mint authority active", "severity": "CRITICAL"}]},
        "holders": {"flags": []},
        "market": {"flags": []},
        "contract": {"flags": []},
        "social": {"flags": []}
    }
    summary, verdict = asyncio.run(generate_ai_summary(mock_pillars))
    assert isinstance(summary, str) and len(summary) > 10
    assert verdict in ["SAFE", "CAUTION", "HIGH RISK", "LIKELY RUG"]

def test_db_save_and_retrieve():
    test_id = "test-uuid-12345"
    test_mint = "So11111111111111111111111111111111111111112"
    report_data = {
        "report_id": test_id,
        "mint_address": test_mint,
        "token_name": "Wrapped SOL",
        "token_symbol": "SOL",
        "generated_at": "2026-09-08T20:00:00Z",
        "overall_score": 95,
        "verdict": "SAFE",
        "pillars": {"security": {"score": 95, "flags": []}},
        "ai_summary": "Wrapped SOL is the canonical wrapped token on Solana.",
        "shareable_url": f"/report/{test_id}"
    }

    asyncio.run(save_report(report_data))
    retrieved = asyncio.run(get_report_by_id(test_id))
    assert retrieved is not None
    assert retrieved["report_id"] == test_id
    assert retrieved["token_symbol"] == "SOL"

def test_known_address_cex_exclusion_from_concentration():
    from services.known_addresses import identify_known_address
    # Test lookup directly
    binance_match = identify_known_address("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
    assert binance_match is not None
    assert binance_match["name"] == "Binance Custody"
    assert binance_match["exclude_from_concentration"] is True

    # Test scoring with Binance (26%) and Raydium (12%)
    onchain_data = {
        "mint_authority_revoked": True,
        "freeze_authority_revoked": True,
        "token_program": "SPL Token",
        "holders": [
            {"address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "percentage": 26.0},  # Binance Custody
            {"address": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1", "percentage": 12.0},  # Raydium AMM
            {"address": "IndividualWallet11111111111111111111111111111", "percentage": 4.0},
            {"address": "IndividualWallet22222222222222222222222222222", "percentage": 3.0}
        ]
    }
    market_data = {
        "liquidity_usd": 500000.0,
        "volume_24h": 200000.0,
        "price_usd": 0.05,
        "price_history": [0.05] * 7,
        "lp_unlocked": False,
        "holder_count": 85000,
        "unique_traders_24h": 1250,
        "trades_24h": 4500
    }
    social_data = {
        "website": "https://example.com",
        "twitter": "https://x.com/example",
        "telegram": "https://t.me/example"
    }

    pillars, overall_score, verdict = calculate_pillar_scores(onchain_data, market_data, social_data)

    holders_pillar = pillars["holders"]
    # Verify Binance & Raydium did not collapse holder score
    assert holders_pillar["score"] == 100, f"Expected 100, got {holders_pillar['score']}"
    assert holders_pillar["cex_dex_percentage"] == 38.0
    assert holders_pillar["insider_top_10_percentage"] == 7.0
    # Verify positive info flag was added for institutional custody
    info_flags = [f for f in holders_pillar["flags"] if f["severity"] == "INFO"]
    assert any("institutional custody" in f["label"].lower() for f in info_flags)

    # Verify market unique traders passed through
    assert pillars["market"]["unique_traders_24h"] == 1250
    assert pillars["market"]["trades_24h"] == 4500

def test_unknown_individual_whale_triggers_penalty():
    onchain_data = {
        "mint_authority_revoked": True,
        "freeze_authority_revoked": True,
        "token_program": "SPL Token",
        "holders": [
            {"address": "UnknownRogueWhale1111111111111111111111111111111", "percentage": 35.0},
            {"address": "UnknownRogueWhale2222222222222222222222222222222", "percentage": 20.0},
            {"address": "IndividualWallet3333333333333333333333333333333", "percentage": 10.0}
        ]
    }
    market_data = {
        "liquidity_usd": 100000.0,
        "volume_24h": 50000.0,
        "price_usd": 1.0,
        "price_history": [1.0] * 7,
        "lp_unlocked": False
    }
    social_data = {
        "website": "https://example.com",
        "twitter": "https://x.com/example",
        "telegram": "https://t.me/example"
    }

    pillars, overall_score, verdict = calculate_pillar_scores(onchain_data, market_data, social_data)
    # 35% single wallet (-25) + 65% top 10 (-30) -> holders_score <= 45
    assert pillars["holders"]["score"] <= 50
    critical_or_warn = [f for f in pillars["holders"]["flags"] if f["severity"] in ["CRITICAL", "WARNING"]]
    assert len(critical_or_warn) >= 2

def test_resolve_token_account_owner_and_cex_matching(monkeypatch):
    from services.onchain import resolve_token_account_owners
    from services.known_addresses import identify_known_address

    # Mock rpc_call to simulate getMultipleAccounts returning parsed TokenAccount
    # where ATA is ATA_BINANCE_XYZ and owner is 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM (Binance Custody)
    async def mock_rpc_call(method, params):
        if method == "getMultipleAccounts":
            return {
                "result": {
                    "value": [
                        {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "owner": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                                        "tokenAmount": {"uiAmount": 5000000.0}
                                    }
                                }
                            }
                        },
                        {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "owner": "SomeIndividualWalletPubkey12345678901234567",
                                        "tokenAmount": {"uiAmount": 100000.0}
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        return {"result": {"value": None}}

    import services.onchain as onchain_module
    monkeypatch.setattr(onchain_module, "rpc_call", mock_rpc_call)

    raw_token_accounts = [
        {"address": "ATA_BINANCE_XYZ_11111111111111111111111111", "uiAmount": 5000000.0},
        {"address": "ATA_INDIVIDUAL_222222222222222222222222222", "uiAmount": 100000.0}
    ]

    resolved = asyncio.run(resolve_token_account_owners(raw_token_accounts))
    assert len(resolved) == 2

    # Account 0: ATA_BINANCE -> owner is Binance Custody
    acc0 = resolved[0]
    assert acc0["owner"] == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    known0 = identify_known_address(acc0["owner"])
    assert known0 is not None
    assert known0["name"] == "Binance Custody"
    assert known0["exclude_from_concentration"] is True

    # Account 1: ATA_INDIVIDUAL -> unverified individual
    acc1 = resolved[1]
    assert acc1["owner"] == "SomeIndividualWalletPubkey12345678901234567"
    known1 = identify_known_address(acc1["owner"])
    assert known1 is None

def test_canonical_usdc_scoring():
    from services.asset_registry import get_asset_classification
    usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    asset_meta = get_asset_classification(usdc_mint)
    assert asset_meta["asset_type"] == "STABLECOIN"
    assert asset_meta["issuer"] == "Circle Financial Inc."
    assert asset_meta["is_canonical"] is True

    # USDC onchain data: active mint authority and active freeze authority
    onchain_data = {
        "mint_address": usdc_mint,
        "token_name": "USD Coin",
        "token_symbol": "USDC",
        "mint_authority_revoked": False,  # Active mint authority (Circle master minter)
        "freeze_authority_revoked": False,  # Active freeze authority (sanctions compliance)
        "token_program": "SPL Token",
        "holders": [
            {"address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", "percentage": 15.0}, # Binance
            {"address": "IndividualWallet11111111111111111111111111111", "percentage": 2.0}
        ]
    }
    market_data = {
        "liquidity_usd": 50000000.0,
        "volume_24h": 25000000.0,
        "price_usd": 1.0,
        "price_history": [1.0] * 7,
        "lp_unlocked": True,  # Multi-DEX liquidity pools, not burned memecoin LP
        "holder_count": 2500000,
        "unique_traders_24h": 45000,
        "trades_24h": 120000
    }
    social_data = {
        "website": None,  # Will adopt Circle registry website
        "twitter": None,
        "telegram": None  # Corporate entity, no retail TG
    }

    pillars, overall_score, verdict = calculate_pillar_scores(
        onchain_data, market_data, social_data, asset_meta=asset_meta
    )

    # Security score must NOT be penalized
    assert pillars["security"]["score"] == 100
    # Overall score must NOT be capped at 30!
    assert overall_score >= 90, f"Expected overall_score >= 90, got {overall_score}"
    assert verdict == "SAFE"

    sec_flags = [f["label"] for f in pillars["security"]["flags"]]
    assert any("reserve elasticity" in f for f in sec_flags)
    assert any("regulatory and sanctions compliance" in f for f in sec_flags)

def test_canonical_wsol_scoring():
    from services.asset_registry import get_asset_classification
    wsol_mint = "So11111111111111111111111111111111111111112"
    asset_meta = get_asset_classification(wsol_mint)
    assert asset_meta["asset_type"] == "WRAPPED"
    assert asset_meta["is_canonical"] is True

    onchain_data = {
        "mint_address": wsol_mint,
        "token_name": "Wrapped SOL",
        "token_symbol": "SOL",
        "mint_authority_revoked": False,
        "freeze_authority_revoked": True,
        "token_program": "SPL Token",
        "holders": []
    }
    market_data = {
        "liquidity_usd": 100000000.0,
        "volume_24h": 50000000.0,
        "price_usd": 140.0,
        "price_history": [140.0] * 7,
        "lp_unlocked": True
    }
    social_data = {"website": None, "twitter": None, "telegram": None}

    pillars, overall_score, verdict = calculate_pillar_scores(
        onchain_data, market_data, social_data, asset_meta=asset_meta
    )

    assert pillars["security"]["score"] == 100
    assert overall_score >= 90
    assert verdict == "SAFE"

def test_standard_spl_retains_strict_memecoin_penalties():
    from services.asset_registry import get_asset_classification
    random_mint = "SomeRandomMemeCoinMint1111111111111111111111111"
    asset_meta = get_asset_classification(random_mint)
    assert asset_meta["asset_type"] == "STANDARD_SPL"
    assert asset_meta["is_canonical"] is False

    onchain_data = {
        "mint_address": random_mint,
        "token_name": "Scam Coin",
        "token_symbol": "SCAM",
        "mint_authority_revoked": False,  # Active mint authority on memecoin
        "freeze_authority_revoked": False, # Active freeze authority
        "token_program": "SPL Token",
        "holders": [{"address": "Whale1", "percentage": 50.0}]
    }
    market_data = {
        "liquidity_usd": 1000.0,
        "volume_24h": 200.0,
        "price_usd": 0.0001,
        "price_history": [0.0001] * 7,
        "lp_unlocked": True
    }
    social_data = {"website": None, "twitter": None, "telegram": None}

    pillars, overall_score, verdict = calculate_pillar_scores(
        onchain_data, market_data, social_data, asset_meta=asset_meta
    )

    # Standard memecoin penalties must apply
    assert pillars["security"]["score"] == 0
    assert overall_score <= 30
    assert verdict in ["HIGH RISK", "LIKELY RUG"]


