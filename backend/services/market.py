import os
import httpx
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

BIRDEYE_API_KEY = os.environ.get("BIRDEYE_API_KEY", "").strip()

async def fetch_market_data(mint_address: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """
    Fetches real live market metrics (liquidity, volume, price, historical candles)
    using BirdEye and DexScreener. Zero mock data.
    """
    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        should_close = True

    market_data = {
        "available": True,
        "price_usd": 0.0,
        "liquidity_usd": 0.0,
        "volume_24h": 0.0,
        "market_cap_usd": 0.0,
        "price_history": [],
        "lp_unlocked": False,
        "token_name": None,
        "token_symbol": None,
        "holder_count": None,
        "unique_traders_24h": None,
        "trades_24h": None
    }

    try:
        # 1. Real BirdEye Token Overview
        if BIRDEYE_API_KEY:
            try:
                headers = {"X-API-KEY": BIRDEYE_API_KEY, "x-chain": "solana"}
                be_url = f"https://public-api.birdeye.so/defi/token_overview?address={mint_address}"
                be_res = await client.get(be_url, headers=headers, timeout=6.0)
                if be_res.status_code == 200:
                    be_json = be_res.json()
                    data = be_json.get("data") or {}
                    
                    price = float(data.get("price") or 0.0)
                    liq = float(data.get("liquidity") or 0.0)
                    vol24 = float(data.get("v24hUSD") or 0.0)
                    mcap = float(data.get("marketCap") or data.get("fdv") or 0.0)

                    market_data["price_usd"] = price
                    market_data["liquidity_usd"] = liq
                    market_data["volume_24h"] = vol24
                    market_data["market_cap_usd"] = mcap
                    market_data["holder_count"] = data.get("holder")

                    if data.get("uniqueWallet24h") is not None:
                        try:
                            market_data["unique_traders_24h"] = int(data.get("uniqueWallet24h"))
                        except Exception:
                            pass

                    if data.get("trade24h") is not None:
                        try:
                            market_data["trades_24h"] = int(data.get("trade24h"))
                        except Exception:
                            pass

                    if data.get("name"):
                        market_data["token_name"] = data["name"]
                    if data.get("symbol"):
                        market_data["token_symbol"] = data["symbol"]

                    # Extract real chronological historical price points from BirdEye
                    history_keys = [
                        "history24hPrice", "history8hPrice", "history4hPrice",
                        "history2hPrice", "history1hPrice", "history30mPrice",
                        "history5mPrice", "price"
                    ]
                    real_candles = []
                    for k in history_keys:
                        val = data.get(k)
                        if val is not None and float(val) > 0:
                            real_candles.append(float(val))
                    if real_candles:
                        market_data["price_history"] = real_candles

                    if liq < 5000:
                        market_data["lp_unlocked"] = True
            except Exception as e:
                print(f"BirdEye overview error: {e}")

        # 2. DexScreener (Real pool and pair data)
        try:
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
            res = await client.get(dex_url, timeout=6.0)
            if res.status_code == 200:
                body = res.json()
                pairs = body.get("pairs") or []
                if pairs:
                    pairs.sort(key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
                    top_pair = pairs[0]
                    base = top_pair.get("baseToken", {})
                    quote = top_pair.get("quoteToken", {})

                    # Properly distinguish whether target mint is baseToken or quoteToken
                    is_base = (base.get("address") == mint_address)
                    target_token = base if is_base else quote

                    target_name = target_token.get("name")
                    raw_symbol = target_token.get("symbol")
                    target_symbol = str(raw_symbol).lstrip("$") if raw_symbol else None

                    if not market_data["token_name"] and target_name:
                        market_data["token_name"] = target_name
                    if not market_data["token_symbol"] and target_symbol:
                        market_data["token_symbol"] = target_symbol

                    # Target price:
                    # If target is baseToken, top_pair.get("priceUsd") is target's USD price.
                    # If target is quoteToken, priceUsd in the pair is the BASE token's price.
                    if market_data["price_usd"] == 0.0:
                        if is_base:
                            market_data["price_usd"] = float(top_pair.get("priceUsd") or 0.0)
                        else:
                            from services.asset_registry import get_asset_classification
                            asset_info = get_asset_classification(mint_address)
                            if asset_info.get("expected_price_usd"):
                                market_data["price_usd"] = float(asset_info["expected_price_usd"])

                    # If not already populated from BirdEye, use DexScreener real metrics
                    if market_data["liquidity_usd"] == 0.0:
                        market_data["liquidity_usd"] = float(top_pair.get("liquidity", {}).get("usd", 0.0) or 0.0)
                    if market_data["volume_24h"] == 0.0:
                        market_data["volume_24h"] = float(top_pair.get("volume", {}).get("h24", 0.0) or 0.0)
                    if market_data["market_cap_usd"] == 0.0:
                        market_data["market_cap_usd"] = float(top_pair.get("fdv", 0.0) or 0.0)

                    # Extract 24h txns as fallback
                    txns_h24 = top_pair.get("txns", {}).get("h24", {})
                    buys = int(txns_h24.get("buys") or 0)
                    sells = int(txns_h24.get("sells") or 0)
                    total_txns = buys + sells
                    if market_data["trades_24h"] is None and total_txns > 0:
                        market_data["trades_24h"] = total_txns
                    if market_data["unique_traders_24h"] is None and total_txns > 0:
                        market_data["unique_traders_24h"] = total_txns

                    if market_data["liquidity_usd"] < 5000:
                        market_data["lp_unlocked"] = True
        except Exception as e:
            print(f"DexScreener fetch error: {e}")

        # Check canonical asset registry to reinforce metadata if missing
        from services.asset_registry import get_asset_classification
        asset_reg = get_asset_classification(mint_address)
        if asset_reg.get("is_canonical"):
            if asset_reg.get("canonical_name") and not market_data["token_name"]:
                market_data["token_name"] = asset_reg["canonical_name"]
            if asset_reg.get("canonical_symbol") and not market_data["token_symbol"]:
                market_data["token_symbol"] = asset_reg["canonical_symbol"]
            if market_data["price_usd"] == 0.0 and asset_reg.get("expected_price_usd"):
                market_data["price_usd"] = float(asset_reg["expected_price_usd"])

        # If price history is still empty, populate with current price point if available
        if not market_data["price_history"] and market_data["price_usd"] > 0:
            market_data["price_history"] = [market_data["price_usd"]]

    except Exception as e:
        market_data["available"] = False
        print(f"Market data general error: {e}")
    finally:
        if should_close:
            await client.aclose()

    return market_data
