from typing import Dict, Any, List, Tuple, Optional
from services.known_addresses import identify_known_address
from services.asset_registry import get_asset_classification

def calculate_pillar_scores(
    onchain_data: Dict[str, Any],
    market_data: Dict[str, Any],
    social_data: Dict[str, Any],
    asset_meta: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], int, str]:
    """
    Computes scores and flags for all pillars, applies weighting and auto-rules,
    and returns (pillars_dict, overall_score, verdict).
    Supports contextual scoring for STABLECOIN, WRAPPED, and STANDARD_SPL assets.
    """
    if asset_meta is None:
        mint_addr = onchain_data.get("mint_address") or onchain_data.get("mint_info", {}).get("mint_address") or ""
        asset_meta = get_asset_classification(mint_addr)

    asset_type = asset_meta.get("asset_type", "STANDARD_SPL")
    is_stablecoin = (asset_type == "STABLECOIN")
    is_wrapped = (asset_type == "WRAPPED")
    is_canonical = asset_meta.get("is_canonical", False)
    issuer = asset_meta.get("issuer")

    # -------------------------------------------------------------
    # 1. SECURITY PILLAR (Weight: 35%)
    # -------------------------------------------------------------
    sec_score = 100
    sec_flags = []
    
    mint_info = onchain_data.get("mint_info") or {}
    if "mint_authority_enabled" in mint_info:
        mint_revoked = not mint_info["mint_authority_enabled"]
    else:
        mint_revoked = onchain_data.get("mint_authority_revoked", True)

    if "freeze_authority_enabled" in mint_info:
        freeze_revoked = not mint_info["freeze_authority_enabled"]
    else:
        freeze_revoked = onchain_data.get("freeze_authority_revoked", True)

    lp_unlocked = market_data.get("lp_unlocked", False)
    
    # 1A. Mint Authority Evaluation
    if not mint_revoked:
        if is_stablecoin:
            sec_flags.append({
                "label": "Mint authority retained by verified issuer for reserve elasticity",
                "severity": "INFO"
            })
        elif is_wrapped:
            sec_flags.append({
                "label": "Mint authority managed by canonical wrapped asset program",
                "severity": "INFO"
            })
        else:
            sec_score -= 50
            sec_flags.append({
                "label": "Mint authority is ENABLED (unlimited new tokens can be minted)",
                "severity": "CRITICAL"
            })
    else:
        sec_flags.append({
            "label": "Mint authority is permanently revoked",
            "severity": "INFO"
        })

    # 1B. Freeze Authority Evaluation
    if not freeze_revoked:
        if is_stablecoin:
            sec_flags.append({
                "label": "Freeze authority retained for regulatory and sanctions compliance",
                "severity": "INFO"
            })
        elif is_wrapped:
            sec_flags.append({
                "label": "Freeze authority managed for system program compatibility",
                "severity": "INFO"
            })
        else:
            sec_score -= 25
            sec_flags.append({
                "label": "Freeze authority is ENABLED (holder accounts can be blacklisted/frozen)",
                "severity": "WARNING"
            })
    else:
        sec_flags.append({
            "label": "Freeze authority is permanently revoked",
            "severity": "INFO"
        })

    # 1C. Liquidity Lock / Burn Evaluation
    if lp_unlocked:
        if is_stablecoin:
            sec_flags.append({
                "label": "Institutional asset backed by centralized issuer and cross-DEX liquidity",
                "severity": "INFO"
            })
        elif is_wrapped:
            sec_flags.append({
                "label": "Canonical asset liquidity distributed natively across all Solana pairs",
                "severity": "INFO"
            })
        else:
            sec_score -= 40
            sec_flags.append({
                "label": "Liquidity pool is UNLOCKED or unburned (high rug-pull risk)",
                "severity": "CRITICAL"
            })
    else:
        sec_flags.append({
            "label": "Liquidity pool tokens burned or securely locked",
            "severity": "INFO"
        })

    sec_score = max(0, min(100, sec_score))
    
    security_pillar = {
        "score": sec_score,
        "flags": sec_flags,
        "mint_authority_revoked": mint_revoked,
        "freeze_authority_revoked": freeze_revoked,
        "lp_burned_or_locked": not lp_unlocked,
        "asset_classification": asset_type,
        "issuer": issuer
    }

    # -------------------------------------------------------------
    # 2. HOLDERS PILLAR (Weight: 25%)
    # -------------------------------------------------------------
    holders_score = 100
    holders_flags = []
    top_holders = onchain_data.get("holders") or onchain_data.get("top_holders", [])

    # Annotate any unannotated holders with known entity metadata
    for h in top_holders:
        if "exclude_from_concentration" not in h:
            owner = h.get("owner")
            ata = h.get("token_account")
            addr = h.get("address", "")
            known = (identify_known_address(owner) if owner else None) or identify_known_address(ata) or identify_known_address(addr)
            h["label"] = known["name"] if known else None
            h["category"] = known["category"] if known else "INDIVIDUAL"
            h["is_known_entity"] = known is not None
            h["exclude_from_concentration"] = known.get("exclude_from_concentration", False) if known else False

    # Aggregate total top-10 concentration for transparency
    top_10_sum = sum(h.get("percentage", 0) for h in top_holders[:10])
    
    # Identify institutional custody (CEX) and DEX liquidity pool reserves
    cex_dex_holders = [h for h in top_holders if h.get("exclude_from_concentration")]
    cex_dex_sum = sum(h.get("percentage", 0) for h in cex_dex_holders)

    # Insider wallets subject to concentration risk penalty
    insider_wallets = [h for h in top_holders if not h.get("exclude_from_concentration")]
    insider_top_10_sum = sum(h.get("percentage", 0) for h in insider_wallets[:10])
    insider_top_1 = insider_wallets[0].get("percentage", 0) if insider_wallets else 0

    # Penalties strictly applied to unverified/insider wallets
    if insider_top_10_sum > 70:
        holders_score -= 50
        holders_flags.append({
            "label": f"Extreme insider concentration ({insider_top_10_sum:.1f}% owned by top individual wallets)",
            "severity": "CRITICAL"
        })
    elif insider_top_10_sum > 45:
        holders_score -= 30
        holders_flags.append({
            "label": f"High insider concentration ({insider_top_10_sum:.1f}% owned by top individual wallets)",
            "severity": "WARNING"
        })
    else:
        holders_flags.append({
            "label": f"Balanced insider distribution ({insider_top_10_sum:.1f}% across top individual wallets)",
            "severity": "INFO"
        })

    if insider_top_1 > 25:
        holders_score -= 25
        holders_flags.append({
            "label": f"Single individual whale holds dominant stake ({insider_top_1:.1f}% of supply)",
            "severity": "CRITICAL"
        })
    elif insider_top_1 > 12:
        holders_score -= 15
        holders_flags.append({
            "label": f"Largest individual holder holds {insider_top_1:.1f}% of supply",
            "severity": "WARNING"
        })

    # Positive signal for recognized institutional custody / liquidity pools
    if cex_dex_holders:
        names = list(dict.fromkeys([h.get("label") or "Known Entity" for h in cex_dex_holders]))
        holders_flags.append({
            "label": f"Recognized institutional custody / liquidity pools detected ({cex_dex_sum:.1f}% of supply): {', '.join(names[:3])}",
            "severity": "INFO"
        })

    holders_score = max(0, min(100, holders_score))
    real_holder_count = market_data.get("holder_count")
    holders_pillar = {
        "score": holders_score,
        "flags": holders_flags,
        "top_holders": top_holders[:10],
        "top_10_percentage": round(top_10_sum, 2),
        "insider_top_10_percentage": round(insider_top_10_sum, 2),
        "cex_dex_percentage": round(cex_dex_sum, 2),
        "total_holders_count": real_holder_count
    }

    # -------------------------------------------------------------
    # 3. MARKET HEALTH PILLAR (Weight: 15%)
    # -------------------------------------------------------------
    market_score = 100
    market_flags = []
    liq = market_data.get("liquidity_usd", 0.0)
    vol = market_data.get("volume_24h", 0.0)

    if liq < 5000:
        market_score -= 60
        market_flags.append({
            "label": f"Dangerously low liquidity depth (${liq:,.0f} USD)",
            "severity": "CRITICAL"
        })
    elif liq < 25000:
        market_score -= 30
        market_flags.append({
            "label": f"Low liquidity depth (${liq:,.0f} USD), high slippage expected",
            "severity": "WARNING"
        })
    else:
        market_flags.append({
            "label": f"Healthy onchain liquidity (${liq:,.0f} USD)",
            "severity": "INFO"
        })

    if vol < 2000:
        market_score -= 20
        market_flags.append({
            "label": f"Sluggish 24h trading volume (${vol:,.0f} USD)",
            "severity": "WARNING"
        })
    else:
        market_flags.append({
            "label": f"Active 24h trading volume (${vol:,.0f} USD)",
            "severity": "INFO"
        })

    market_score = max(0, min(100, market_score))
    market_pillar = {
        "score": market_score,
        "flags": market_flags,
        "liquidity_usd": liq,
        "volume_24h": vol,
        "price_usd": market_data.get("price_usd", 0.0),
        "market_cap_usd": market_data.get("market_cap_usd", 0.0),
        "unique_traders_24h": market_data.get("unique_traders_24h"),
        "trades_24h": market_data.get("trades_24h"),
        "price_history": market_data.get("price_history", [])
    }

    # -------------------------------------------------------------
    # 4. CONTRACT INTELLIGENCE PILLAR (Weight: 10%)
    # -------------------------------------------------------------
    contract_score = 95
    contract_flags = []
    token_program = onchain_data.get("token_program", "SPL Token")
    is_mutable = onchain_data.get("is_metadata_mutable", False)

    contract_flags.append({
        "label": f"Standard Solana Program: {token_program}",
        "severity": "INFO"
    })

    if is_mutable:
        contract_score -= 30
        contract_flags.append({
            "label": "Token metadata is mutable (metadata and logos can be modified)",
            "severity": "WARNING"
        })
    else:
        contract_flags.append({
            "label": "Token metadata is immutable and verified",
            "severity": "INFO"
        })

    contract_score = max(0, min(100, contract_score))
    contract_pillar = {
        "score": contract_score,
        "flags": contract_flags,
        "token_program": token_program,
        "is_metadata_mutable": is_mutable
    }

    # -------------------------------------------------------------
    # 5. SOCIAL VALIDITY PILLAR (Weight: 15%)
    # -------------------------------------------------------------
    social_score = 100
    social_flags = []
    
    website = social_data.get("website") or asset_meta.get("website")
    twitter = social_data.get("twitter") or asset_meta.get("twitter")
    telegram = social_data.get("telegram")

    if issuer:
        social_flags.append({
            "label": f"Verified Institutional Issuer: {issuer}",
            "severity": "INFO"
        })

    if not website:
        social_score -= 40
        social_flags.append({
            "label": "No official website found in onchain/token registry",
            "severity": "WARNING"
        })
    else:
        social_flags.append({
            "label": f"Official website linked: {website}",
            "severity": "INFO"
        })

    if not twitter:
        social_score -= 35
        social_flags.append({
            "label": "No Twitter/X profile linked to token metadata",
            "severity": "WARNING"
        })
    else:
        social_flags.append({
            "label": "Official Twitter/X community linked",
            "severity": "INFO"
        })

    if not telegram:
        if not is_canonical:
            social_score -= 25
            social_flags.append({
                "label": "No Telegram discussion channel linked",
                "severity": "WARNING"
            })
        else:
            social_flags.append({
                "label": "Institutional issuer uses official corporate communications",
                "severity": "INFO"
            })
    else:
        social_flags.append({
            "label": "Telegram community group verified",
            "severity": "INFO"
        })

    social_score = max(0, min(100, social_score))
    social_pillar = {
        "score": social_score,
        "flags": social_flags,
        "website": website,
        "twitter": twitter,
        "telegram": telegram,
        "discord": social_data.get("discord")
    }

    # -------------------------------------------------------------
    # OVERALL SCORE COMPUTATION (Weights: 35/25/15/10/15)
    # -------------------------------------------------------------
    raw_overall = (
        (sec_score * 0.35) +
        (holders_score * 0.25) +
        (market_score * 0.15) +
        (contract_score * 0.10) +
        (social_score * 0.15)
    )
    overall_score = int(round(raw_overall))

    # Auto-Rules:
    # 1. Mint authority enabled -> automatic cap of 30/100 (Bypassed for canonical/stablecoins)
    if not mint_revoked and (not is_canonical) and (not is_stablecoin) and (not is_wrapped):
        overall_score = min(overall_score, 30)

    # Determine Base Verdict
    if overall_score >= 80:
        verdict = "SAFE"
    elif overall_score >= 50:
        verdict = "CAUTION"
    elif overall_score >= 25:
        verdict = "HIGH RISK"
    else:
        verdict = "LIKELY RUG"

    # Auto-Rule: Both mint authority enabled AND LP unlocked -> verdict forced to HIGH RISK minimum (Bypassed for canonical/stablecoins)
    if (not mint_revoked) and lp_unlocked and (not is_canonical) and (not is_stablecoin) and (not is_wrapped):
        if verdict in ["SAFE", "CAUTION"]:
            verdict = "HIGH RISK"
        if overall_score < 25:
            verdict = "LIKELY RUG"

    pillars = {
        "security": security_pillar,
        "holders": holders_pillar,
        "market": market_pillar,
        "contract": contract_pillar,
        "social": social_pillar,
        "asset_classification": asset_type,
        "issuer": issuer,
        "is_canonical": is_canonical
    }

    return pillars, overall_score, verdict
