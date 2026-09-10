from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])

class WatchlistAddRequest(BaseModel):
    mint_address: str = Field(..., min_length=32, max_length=44, description="Solana mint address")
    name: Optional[str] = "Unknown Token"
    symbol: Optional[str] = "TOKEN"
    category: Optional[str] = "Custom"

# In-memory watchlist store for demo / convenience
_watchlist: List[Dict[str, Any]] = [
    {
        "mint_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "name": "Bonk",
        "symbol": "BONK",
        "category": "Meme"
    },
    {
        "mint_address": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
        "name": "Jupiter",
        "symbol": "JUP",
        "category": "DEX / DeFi"
    },
    {
        "mint_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "name": "USD Coin",
        "symbol": "USDC",
        "category": "Stablecoin"
    }
]

@router.get("")
async def get_watchlist():
    return {"watchlist": _watchlist, "count": len(_watchlist)}

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(item: WatchlistAddRequest):
    mint = item.mint_address.strip()
    # Check if already in watchlist
    for entry in _watchlist:
        if entry["mint_address"] == mint:
            return {"message": "Token already in watchlist", "watchlist": _watchlist}
    
    new_entry = {
        "mint_address": mint,
        "name": item.name or "Unknown Token",
        "symbol": (item.symbol or "TOKEN").lstrip("$"),
        "category": item.category or "Custom"
    }
    _watchlist.append(new_entry)
    return {"message": "Token added to watchlist", "entry": new_entry, "watchlist": _watchlist}

@router.delete("/{mint_address}")
async def remove_from_watchlist(mint_address: str):
    global _watchlist
    mint = mint_address.strip()
    initial_len = len(_watchlist)
    _watchlist = [e for e in _watchlist if e["mint_address"] != mint]
    if len(_watchlist) == initial_len:
        raise HTTPException(status_code=404, detail="Token not found in watchlist")
    return {"message": "Token removed from watchlist", "watchlist": _watchlist}

