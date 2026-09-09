from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])

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
    return {"watchlist": _watchlist}
