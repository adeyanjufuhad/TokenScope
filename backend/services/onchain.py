import httpx
import os
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from services.known_addresses import identify_known_address

load_dotenv()

SOLANA_RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://rpc.ankr.com/solana")
FALLBACK_RPC_URL = "https://api.mainnet-beta.solana.com"
BIRDEYE_API_KEY = os.environ.get("BIRDEYE_API_KEY", "").strip()

_last_call_time = 0.0
_rpc_lock = asyncio.Lock()

async def rpc_call(method: str, params: list) -> dict:
    """
    Make a single JSON-RPC call to the Solana RPC endpoint with 0.5s rate-limit spacing.
    """
    global _last_call_time
    async with _rpc_lock:
        try:
            loop = asyncio.get_event_loop()
            now = loop.time()
            elapsed = now - _last_call_time
            if elapsed < 0.5:
                await asyncio.sleep(0.5 - elapsed)
            _last_call_time = loop.time()
        except Exception:
            pass

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        headers = {"Content-Type": "application/json"}
        endpoints = [SOLANA_RPC_URL, FALLBACK_RPC_URL]

        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            for ep in endpoints:
                try:
                    response = await client.post(ep, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        if "error" not in res_json or res_json.get("result"):
                            return res_json
                except Exception:
                    continue

            response = await client.post(SOLANA_RPC_URL, json=payload)
            response.raise_for_status()
            return response.json()

async def get_token_mint_info(mint_address: str) -> dict:
    """Fetch real mint account info."""
    result = await rpc_call(
        "getAccountInfo",
        [
            mint_address,
            {"encoding": "jsonParsed"}
        ]
    )

    account = result.get("result", {}).get("value", {})
    if not account:
        return {"error": "Token mint not found"}

    parsed = account.get("data", {}).get("parsed", {}).get("info", {})

    mint_authority = parsed.get("mintAuthority")
    freeze_authority = parsed.get("freezeAuthority")

    return {
        "mint_address": mint_address,
        "mint_authority_enabled": mint_authority is not None,
        "mint_authority": mint_authority,
        "freeze_authority_enabled": freeze_authority is not None,
        "freeze_authority": freeze_authority,
        "supply": parsed.get("supply"),
        "decimals": parsed.get("decimals"),
    }

async def get_token_largest_accounts(mint_address: str) -> list:
    """Fetch top holder accounts from Solana RPC."""
    try:
        result = await rpc_call(
            "getTokenLargestAccounts",
            [mint_address]
        )
        accounts = result.get("result", {}).get("value", [])
        return accounts if accounts else []
    except Exception:
        return []

async def get_token_supply(mint_address: str) -> dict:
    """Fetch total token supply from Solana RPC."""
    try:
        result = await rpc_call(
            "getTokenSupply",
            [mint_address]
        )
        value = result.get("result", {}).get("value", {})
        return {
            "total_supply": value.get("uiAmount"),
            "decimals": value.get("decimals")
        }
    except Exception:
        return {"total_supply": None, "decimals": 9}

async def resolve_token_account_owners(token_accounts: list) -> list:
    """
    Given token accounts from getTokenLargestAccounts (which are ATAs/TokenAccounts),
    calls getMultipleAccounts (with getAccountInfo fallback) to parse the TokenAccount
    data structure and extract the actual owner public key.
    """
    if not token_accounts:
        return []

    pubkeys = [acc.get("address") for acc in token_accounts if acc.get("address")]
    if not pubkeys:
        return token_accounts

    values = []
    try:
        res = await rpc_call(
            "getMultipleAccounts",
            [pubkeys, {"encoding": "jsonParsed"}]
        )
        values = res.get("result", {}).get("value") or []
    except Exception as e:
        print(f"getMultipleAccounts error: {e}")
        values = []

    # If getMultipleAccounts failed or was incomplete, fallback to getAccountInfo
    if not values or len(values) != len(pubkeys):
        values = []
        for pk in pubkeys:
            try:
                acc_res = await rpc_call("getAccountInfo", [pk, {"encoding": "jsonParsed"}])
                values.append(acc_res.get("result", {}).get("value"))
            except Exception:
                values.append(None)

    resolved = []
    for idx, acc in enumerate(token_accounts):
        ata_address = acc.get("address", "")
        amount = acc.get("uiAmount") or 0
        owner_address = None

        if idx < len(values) and values[idx]:
            val_item = values[idx]
            if isinstance(val_item, dict):
                data = val_item.get("data")
                if isinstance(data, dict):
                    parsed_info = data.get("parsed", {}).get("info", {})
                    owner_address = parsed_info.get("owner")

        effective_address = owner_address if owner_address else ata_address
        resolved.append({
            "token_account": ata_address,
            "owner": owner_address,
            "address": effective_address,
            "amount": amount
        })

    return resolved

async def fetch_birdeye_holders(mint_address: str) -> List[Dict[str, Any]]:
    """Fetch real top 10 holders from BirdEye API."""
    if not BIRDEYE_API_KEY:
        return []
    try:
        headers = {"X-API-KEY": BIRDEYE_API_KEY, "x-chain": "solana"}
        url = f"https://public-api.birdeye.so/defi/v3/token/holder?address={mint_address}&offset=0&limit=10"
        async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json().get("data", {})
                items = data.get("items", [])
                total_supply = float(data.get("totalSupply", 0) or 0)
                
                parsed = []
                for item in items[:10]:
                    owner = item.get("owner")
                    token_acc = item.get("token_account")
                    addr = owner or token_acc or ""
                    amt = float(item.get("ui_amount") or 0)
                    pct = round((amt / total_supply * 100), 2) if total_supply > 0 else 0.0
                    known = (identify_known_address(owner) if owner else None) or identify_known_address(token_acc) or identify_known_address(addr)
                    parsed.append({
                        "address": addr,
                        "owner": owner,
                        "token_account": token_acc,
                        "amount": amt,
                        "percentage": pct,
                        "label": known["name"] if known else None,
                        "category": known["category"] if known else "INDIVIDUAL",
                        "is_known_entity": known is not None,
                        "exclude_from_concentration": known.get("exclude_from_concentration", False) if known else False
                    })
                return parsed
    except Exception as e:
        print(f"BirdEye holders fetch note: {e}")
    return []

async def get_token_metadata(mint_address: str) -> dict:
    """Fetch token metadata."""
    try:
        result = await rpc_call(
            "getAccountInfo",
            [
                mint_address,
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ]
        )
        account = result.get("result", {}).get("value")
        if not account:
            return {"name": "Unknown", "symbol": "UNKNOWN", "uri": None}

        parsed_data = account.get("data", {})
        if isinstance(parsed_data, dict):
            info = parsed_data.get("parsed", {}).get("info", {})
            return {
                "name": info.get("name", "Unknown"),
                "symbol": info.get("symbol", "UNKNOWN"),
                "uri": info.get("uri", None)
            }
    except Exception:
        pass
    return {"name": "Unknown", "symbol": "UNKNOWN", "uri": None}

async def get_full_onchain_data(mint_address: str) -> dict:
    """
    Master function â€” fetches real onchain and holder data in parallel.
    No mock data.
    """
    mint_info, largest_accounts, supply = await asyncio.gather(
        get_token_mint_info(mint_address),
        get_token_largest_accounts(mint_address),
        get_token_supply(mint_address),
        return_exceptions=True
    )

    if isinstance(mint_info, Exception):
        mint_info = {"error": str(mint_info)}
    if isinstance(largest_accounts, Exception):
        largest_accounts = []
    if isinstance(supply, Exception):
        supply = {"total_supply": None}

    total_supply = supply.get("total_supply") or 0
    holders = []

    # 1. Use RPC largest accounts if available
    if largest_accounts and total_supply > 0:
        # Resolve top 20 accounts from ATAs to actual owner public keys via getMultipleAccounts
        resolved_accounts = await resolve_token_account_owners(largest_accounts[:20])
        for acc in resolved_accounts[:10]:
            amount = acc.get("amount") or 0
            owner = acc.get("owner")
            ata = acc.get("token_account")
            addr = acc.get("address")

            # Match resolved owner public key against known registry
            known = (identify_known_address(owner) if owner else None) or identify_known_address(ata) or identify_known_address(addr)
            holders.append({
                "address": addr,
                "owner": owner,
                "token_account": ata,
                "amount": amount,
                "percentage": round((amount / total_supply) * 100, 2) if total_supply else 0,
                "label": known["name"] if known else None,
                "category": known["category"] if known else "INDIVIDUAL",
                "is_known_entity": known is not None,
                "exclude_from_concentration": known.get("exclude_from_concentration", False) if known else False
            })

    # 2. If RPC was empty or blocked, fetch real holders from BirdEye
    if not holders:
        holders = await fetch_birdeye_holders(mint_address)

    # Ensure all holders have known address attributes and correct percentages
    if holders and total_supply > 0:
        for h in holders:
            if h.get("percentage", 0) == 0 and h.get("amount", 0) > 0:
                h["percentage"] = round((h["amount"] / total_supply) * 100, 2)
            if "exclude_from_concentration" not in h:
                owner = h.get("owner")
                ata = h.get("token_account")
                addr = h.get("address", "")
                known = (identify_known_address(owner) if owner else None) or identify_known_address(ata) or identify_known_address(addr)
                h["label"] = known["name"] if known else None
                h["category"] = known["category"] if known else "INDIVIDUAL"
                h["is_known_entity"] = known is not None
                h["exclude_from_concentration"] = known.get("exclude_from_concentration", False) if known else False

    return {
        "mint_info": mint_info,
        "holders": holders,
        "supply": supply,
        "total_supply": total_supply
    }
