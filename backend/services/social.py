import os
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

BIRDEYE_API_KEY = os.environ.get("BIRDEYE_API_KEY", "").strip()

async def check_url_active(client: httpx.AsyncClient, url: str) -> bool:
    try:
        res = await client.head(url, timeout=3.0, follow_redirects=True)
        return res.status_code < 400
    except Exception:
        try:
            res = await client.get(url, timeout=3.0, follow_redirects=True)
            return res.status_code < 400
        except Exception:
            return False

async def fetch_social_data(mint_address: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """
    Checks real social validity for the token (Website, Twitter/X, Telegram).
    No mock data â€” if not found, returns None.
    """
    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=6.0)
        should_close = True

    social_data = {
        "website": None,
        "twitter": None,
        "telegram": None,
        "discord": None,
        "website_valid": False,
        "available": True
    }

    try:
        # 1. Check BirdEye Token Overview Extensions (official registered socials)
        if BIRDEYE_API_KEY:
            try:
                headers = {"X-API-KEY": BIRDEYE_API_KEY, "x-chain": "solana"}
                be_url = f"https://public-api.birdeye.so/defi/token_overview?address={mint_address}"
                be_res = await client.get(be_url, headers=headers, timeout=5.0)
                if be_res.status_code == 200:
                    ext = be_res.json().get("data", {}).get("extensions") or {}
                    if ext.get("website"):
                        social_data["website"] = ext.get("website")
                    if ext.get("twitter"):
                        social_data["twitter"] = ext.get("twitter")
                    if ext.get("telegram"):
                        social_data["telegram"] = ext.get("telegram")
                    if ext.get("discord"):
                        social_data["discord"] = ext.get("discord")
            except Exception as e:
                print(f"BirdEye social check note: {e}")

        # 2. Check DexScreener info (real community profiles indexed on DEX)
        try:
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
            res = await client.get(dex_url, timeout=5.0)
            if res.status_code == 200:
                body = res.json()
                pairs = body.get("pairs") or []
                if pairs:
                    info = pairs[0].get("info") or {}
                    websites = info.get("websites") or []
                    socials = info.get("socials") or []

                    if not social_data["website"] and websites:
                        social_data["website"] = websites[0].get("url")

                    for s in socials:
                        sType = s.get("type", "").lower()
                        sUrl = s.get("url", "")
                        if ("twitter" in sType or "x.com" in sUrl or "twitter.com" in sUrl) and not social_data["twitter"]:
                            social_data["twitter"] = sUrl
                        elif ("telegram" in sType or "t.me" in sUrl) and not social_data["telegram"]:
                            social_data["telegram"] = sUrl
                        elif ("discord" in sType or "discord" in sUrl) and not social_data["discord"]:
                            social_data["discord"] = sUrl
        except Exception as e:
            print(f"DexScreener social fetch note: {e}")

        # Validate website if real URL was found
        if social_data["website"]:
            social_data["website_valid"] = await check_url_active(client, social_data["website"])
        else:
            social_data["website_valid"] = False

    except Exception as e:
        print(f"Social check general error: {e}")
    finally:
        if should_close:
            await client.aclose()

    return social_data
