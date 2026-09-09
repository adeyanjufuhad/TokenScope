"""
Canonical Asset Registry & Classification Pre-Processor
Maps regulated stablecoins and canonical wrapped assets to prevent false-positive
rug/scam flags and apply asset-specific contextual due diligence.
"""

from typing import Dict, Any, Optional

KNOWN_ASSET_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # 1. REGULATED STABLECOINS
    # -------------------------------------------------------------
    # USDC - USD Coin
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
        "canonical_name": "USD Coin",
        "canonical_symbol": "USDC",
        "asset_type": "STABLECOIN",
        "issuer": "Circle Financial Inc.",
        "website": "https://www.circle.com/en/usdc",
        "twitter": "https://x.com/circle",
        "description": "Regulated US-dollar backed stablecoin issued by Circle with 1:1 liquid fiat/treasury reserves.",
        "is_canonical": True,
        "expected_price_usd": 1.00
    },

    # USDT - Tether USD
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
        "canonical_name": "Tether USD",
        "canonical_symbol": "USDT",
        "asset_type": "STABLECOIN",
        "issuer": "Tether Limited",
        "website": "https://tether.to",
        "twitter": "https://x.com/Tether_to",
        "description": "Fiat-collateralized USD stablecoin issued by Tether with multi-asset reserve backing.",
        "is_canonical": True,
        "expected_price_usd": 1.00
    },

    # PYUSD - PayPal USD
    "2b1kV6ydDS3TCgTgSfvZEoBZa6xQZZmUMzfcvNJydCMj": {
        "canonical_name": "PayPal USD",
        "canonical_symbol": "PYUSD",
        "asset_type": "STABLECOIN",
        "issuer": "Paxos Trust",
        "website": "https://paxos.com/pyusd",
        "twitter": "https://x.com/Paxos",
        "description": "Regulated USD stablecoin issued by Paxos Trust under New York Department of Financial Services (NYDFS) oversight.",
        "is_canonical": True,
        "expected_price_usd": 1.00
    },

    # -------------------------------------------------------------
    # 2. CANONICAL WRAPPED ASSETS
    # -------------------------------------------------------------
    # WSOL - Wrapped SOL
    "So11111111111111111111111111111111111111112": {
        "canonical_name": "Wrapped SOL",
        "canonical_symbol": "SOL",
        "asset_type": "WRAPPED",
        "issuer": "Solana Labs",
        "website": "https://solana.com",
        "twitter": "https://x.com/solana",
        "description": "Canonical native wrapped Solana token backed 1:1 by native SOL in system custody.",
        "is_canonical": True,
        "expected_price_usd": None
    }
}

def get_asset_classification(mint_address: str) -> Dict[str, Any]:
    """
    Classifies a Solana token mint address.
    Returns canonical metadata if recognized, otherwise defaults to STANDARD_SPL.
    """
    if not mint_address:
        return {
            "mint_address": "",
            "asset_type": "STANDARD_SPL",
            "issuer": None,
            "canonical_name": None,
            "canonical_symbol": None,
            "website": None,
            "twitter": None,
            "description": None,
            "is_canonical": False,
            "expected_price_usd": None
        }

    clean_mint = str(mint_address).strip()
    if clean_mint in KNOWN_ASSET_REGISTRY:
        reg = KNOWN_ASSET_REGISTRY[clean_mint]
        return {
            "mint_address": clean_mint,
            "asset_type": reg["asset_type"],
            "issuer": reg["issuer"],
            "canonical_name": reg["canonical_name"],
            "canonical_symbol": reg["canonical_symbol"],
            "website": reg.get("website"),
            "twitter": reg.get("twitter"),
            "description": reg.get("description"),
            "is_canonical": True,
            "expected_price_usd": reg.get("expected_price_usd")
        }

    return {
        "mint_address": clean_mint,
        "asset_type": "STANDARD_SPL",
        "issuer": None,
        "canonical_name": None,
        "canonical_symbol": None,
        "website": None,
        "twitter": None,
        "description": None,
        "is_canonical": False,
        "expected_price_usd": None
    }
