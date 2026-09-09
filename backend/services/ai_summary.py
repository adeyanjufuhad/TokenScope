import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

SYSTEM_INSTRUCTION = (
    "You are a Solana token risk analyst. You write plain-English risk summaries "
    "for retail investors. Be direct, factual, and concise. Never use jargon. "
    "Always lead with the most important finding.\n\n"
    "CRITICAL CONTEXT ON ASSET CLASSIFICATION:\n"
    "- If asset_classification is STABLECOIN, interpret active mint and freeze authorities as standard regulatory "
    "and reserve-management mechanisms rather than centralization or rug-pull threats. Frame the risk around issuer "
    "solvency, peg stability, and counterparty trust rather than memecoin exit liquidity.\n"
    "- If asset_classification is WRAPPED, understand that it represents canonical wrapped native assets (such as Wrapped SOL) "
    "backed 1:1 by underlying native tokens.\n\n"
    "CRITICAL CONTEXT ON HOLDERS:\n"
    "- Centralized exchange (CEX) custody wallets (e.g. Binance, Coinbase, Bybit, OKX, Gate.io) "
    "and decentralized exchange (DEX) liquidity pools (e.g. Raydium, Orca, Meteora) are institutional "
    "reserves holding customer deposits or automated market liquidity. They are NOT rogue insider whales.\n"
    "- Never treat CEX or DEX holdings as a malicious insider dumping risk or rug-pull threat.\n"
    "- Base insider concentration warnings strictly on individual unverified wallets (insider_top_10_percentage)."
)

def _get_model():
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    # Prioritize active models in environment
    for m_name in ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
        try:
            return genai.GenerativeModel(
                model_name=m_name,
                system_instruction=SYSTEM_INSTRUCTION
            )
        except Exception:
            continue
    return None

def _generate_fallback_summary(pillar_data: dict) -> tuple[str, str]:
    """Generates a structured analytical summary when Gemini API is offline or key is missing."""
    asset_type = pillar_data.get("asset_classification") or pillar_data.get("security", {}).get("asset_classification", "STANDARD_SPL")
    issuer = pillar_data.get("issuer") or pillar_data.get("security", {}).get("issuer")

    if asset_type == "STABLECOIN":
        summary = (
            f"Audit confirms {issuer or 'verified issuer'} canonical stablecoin status. "
            "Mint and freeze authorities are retained for regulatory compliance, sanctions enforcement, and fiat reserve elasticity. "
            "Primary risk considerations center on issuer solvency and reserve backing rather than onchain smart contract rug-pull vectors."
        )
        return summary, "SAFE"
    elif asset_type == "WRAPPED":
        summary = (
            "Audit confirms canonical wrapped asset status backed 1:1 by native Solana reserves. "
            "Technical onchain parameters and liquidity align with network standard requirements. "
            "Counterparty and contract risks are minimal."
        )
        return summary, "SAFE"

    critical_flags = []
    warning_flags = []
    
    for pillar_name, pdata in pillar_data.items():
        if isinstance(pdata, dict) and "flags" in pdata:
            for flag in pdata["flags"]:
                if flag.get("severity") == "CRITICAL":
                    critical_flags.append(f"{flag.get('label')}")
                elif flag.get("severity") == "WARNING":
                    warning_flags.append(f"{flag.get('label')}")

    if critical_flags:
        summary = (
            f"Audit detected critical vulnerabilities including {', '.join(critical_flags[:2])}. "
            "These high-risk vectors present immediate threat of capital loss or malicious liquidity manipulation. "
            "Retail investors should exercise extreme caution before committing capital."
        )
        verdict = "LIKELY RUG" if len(critical_flags) >= 2 else "HIGH RISK"
    elif warning_flags:
        summary = (
            f"Audit identified potential concerns regarding {', '.join(warning_flags[:2])}. "
            "While no immediate rug-pull vectors were confirmed, moderate concentration and liquidity indicators warrant close monitoring. "
            "Proceed with vigilance."
        )
        verdict = "CAUTION"
    else:
        summary = (
            "No high-severity vulnerabilities were detected across security, holder distribution, and contract intelligence. "
            "Mint authority is properly managed, liquidity depth is healthy, and onchain parameters align with established safety benchmarks. "
            "The token demonstrates standard decentralized risk hygiene."
        )
        verdict = "SAFE"

    return summary, verdict

async def generate_ai_summary(pillar_data: dict) -> tuple[str, str]:
    """
    Takes the full pillar data dict and returns (summary_text, verdict).
    Verdict will be one of: SAFE, CAUTION, HIGH RISK, LIKELY RUG
    """
    holders_p = pillar_data.get("holders", {})
    cex_pct = holders_p.get("cex_dex_percentage", 0)
    insider_pct = holders_p.get("insider_top_10_percentage", 0)
    total_top10 = holders_p.get("top_10_percentage", 0)
    
    known_entities = [
        f"{h.get('label')} ({h.get('percentage')}%)"
        for h in holders_p.get("top_holders", [])
        if h.get("is_known_entity") and h.get("label")
    ]
    known_str = ", ".join(known_entities) if known_entities else "None detected"

    asset_classification = pillar_data.get("asset_classification") or pillar_data.get("security", {}).get("asset_classification", "STANDARD_SPL")
    issuer = pillar_data.get("issuer") or pillar_data.get("security", {}).get("issuer")

    if asset_classification == "STABLECOIN":
        asset_guideline = (
            "If asset_classification is STABLECOIN, interpret active mint and freeze authorities as standard regulatory "
            "and reserve-management mechanisms rather than centralization or rug-pull threats. Frame the risk around issuer "
            "solvency, peg stability, and counterparty trust rather than memecoin exit liquidity."
        )
    elif asset_classification == "WRAPPED":
        asset_guideline = (
            "This is a canonical wrapped asset (such as Wrapped SOL) backed 1:1 by native blockchain reserves. "
            "Mint and pool parameters are native protocol mechanics rather than malicious insider vectors."
        )
    else:
        asset_guideline = (
            "Standard SPL token / memecoin rules apply. Retain strict vigilance regarding mint/freeze authorities and unburned liquidity pools."
        )

    prompt = f"""Here is the audit data for a Solana token:

{json.dumps(pillar_data, indent=2)}

CRITICAL ASSET CLASSIFICATION CONTEXT:
- Asset Type: {asset_classification}
- Verified Issuer: {issuer or "Decentralized / Community"}
- ASSET EVALUATION MANDATE: {asset_guideline}

CRITICAL HOLDER AND EXCHANGE RESERVES CONTEXT:
- Total Top 10 Accounts: {total_top10}%
- Recognized CEX Custody & DEX Liquidity Reserves: {cex_pct}% ({known_str})
- Actual Unverified Insider Top-10 Concentration: {insider_pct}%
- MANDATORY INSTRUCTION: The {cex_pct}% held by recognized exchanges and DEX pools represents customer exchange deposits and market liquidity pools, NOT rogue insider whales. You MUST NOT warn about or treat these exchange balances as an insider dump or centralization risk. Base insider concentration assessments solely on the {insider_pct}% held by unverified individual wallets.

Write a 2-3 sentence risk summary for a retail investor. 
Identify the top risk factors explicitly by name.
End your response with a new line containing only the verdict word(s): SAFE, CAUTION, HIGH RISK, or LIKELY RUG.
Do not add any other text after the verdict."""

    if os.environ.get("GEMINI_API_KEY"):
        for m_name in ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
            try:
                m = genai.GenerativeModel(model_name=m_name, system_instruction=SYSTEM_INSTRUCTION)
                response = m.generate_content(prompt)
                full_text = response.text.strip()

                lines = full_text.strip().split("\n")
                verdict_line = lines[-1].strip().upper()

                valid_verdicts = ["SAFE", "CAUTION", "HIGH RISK", "LIKELY RUG"]
                verdict = verdict_line if verdict_line in valid_verdicts else "CAUTION"
                summary = "\n".join(lines[:-1]).strip()

                return summary, verdict
            except Exception as e:
                print(f"Gemini model {m_name} attempt error: {e}")
                continue

    return _generate_fallback_summary(pillar_data)
