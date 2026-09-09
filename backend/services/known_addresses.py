"""
Known Solana Addresses Registry
Maps top CEX custody/hot/cold wallets, DEX program vaults, liquidity pools,
and system burn addresses to prevent false-positive insider concentration penalties.
"""

from typing import Optional, Dict, Any

KNOWN_ADDRESSES: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # 1. CENTRALIZED EXCHANGES (CEX Custody / Hot / Cold Wallets)
    # -------------------------------------------------------------
    # Binance
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": {
        "name": "Binance Custody",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Binance cold custody reserve wallet"
    },
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": {
        "name": "Binance Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Binance active exchange hot wallet"
    },
    "2OJv9BAHjaAssNo7CGDocLaKnCw9xvnDY4t73g2sYv2p": {
        "name": "Binance 3",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Binance settlement wallet"
    },
    "DRpbCBMxVBaWiBPGoc8G6HyUqvSp8hCeStjupAR6rsMW": {
        "name": "Binance 4",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Binance customer deposit wallet"
    },
    "A77HErqtfN1hLLrSQjKstMwLZbLhp2o4B7f9uP86w1bS": {
        "name": "Binance 5",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Binance withdrawal pool"
    },

    # Coinbase
    "H8sMJSCQxfKiFTCfYq4W9fTVUGoWHmauy1PRBP5QFxYn": {
        "name": "Coinbase Cold Storage",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Coinbase institutional cold custody"
    },
    "2AQdpHJ2JpcEgPiATUXjQxA8QmafFegfQwSLWSprPics": {
        "name": "Coinbase Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Coinbase active exchange hot wallet"
    },
    "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE": {
        "name": "Coinbase Custody",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Coinbase prime custody vault"
    },

    # Bybit
    "2Ejnns2Fd5gsZdFJbnkZmQEwbrgoiMc2ikKcS2z2Ps3e": {
        "name": "Bybit Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Bybit exchange operations wallet"
    },
    "AC5RDfQFmDS1deWZos921qbhirGLTgFgSLmjvafUpSTk": {
        "name": "Bybit Custody",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Bybit exchange reserve vault"
    },

    # OKX
    "5VCwKtCXgCJ6kit5FybXjvriW3xSfWXNQVdx3oozkjb2": {
        "name": "OKX Custody",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "OKX institutional reserve wallet"
    },
    "6ZRCB7AAqGrepmRU2BpZZL9NW3LndPDnee4X1bYSjK3F": {
        "name": "OKX Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "OKX active exchange operations"
    },

    # Gate.io
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": {
        "name": "Gate.io Custody",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Gate.io user deposit custody"
    },
    "4xQj6y8AANv233nCGpG8Ebb8t7t29s6k2i8b9tY6c7k": {
        "name": "Gate.io Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Gate.io exchange hot wallet"
    },

    # Kraken
    "FWznbcNXWQuHTawe9RxvQ2LdCENssh12dsznf4RiouN5": {
        "name": "Kraken Cold Storage",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Kraken institutional custody"
    },
    "LBuY2AeqqENH4sE4mJc426E8pXg5mP8wD2aK7sQ9mN1": {
        "name": "Kraken Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "Kraken exchange hot wallet"
    },

    # KuCoin
    "bmwCXs97KxQe9vBvL35m6Ea4nS1f9wD3yA1sK8gP6m": {
        "name": "KuCoin Hot Wallet",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "KuCoin exchange operations"
    },

    # MEXC
    "ASTyfSima4LLAdDgoFGkgqoKowG1LZFDr9fAQrg7iaJZ": {
        "name": "MEXC Custody",
        "category": "CEX",
        "exclude_from_concentration": True,
        "description": "MEXC exchange operations wallet"
    },

    # -------------------------------------------------------------
    # 2. DECENTRALIZED EXCHANGES (DEX Program Vaults & Pools)
    # -------------------------------------------------------------
    # Raydium
    "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": {
        "name": "Raydium AMM Authority",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Raydium AMM V4 authority vault"
    },
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": {
        "name": "Raydium AMM V4",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Raydium AMM V4 liquidity program"
    },
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": {
        "name": "Raydium CLMM",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Raydium concentrated liquidity pool"
    },
    "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": {
        "name": "OpenBook DEX",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "OpenBook / Serum central order book"
    },

    # Orca
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": {
        "name": "Orca Whirlpools",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Orca concentrated liquidity program"
    },
    "9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP": {
        "name": "Orca Swap V2",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Orca AMM pool program"
    },

    # Meteora
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": {
        "name": "Meteora DLMM",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Meteora dynamic liquidity market maker"
    },
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": {
        "name": "Meteora Vault",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Meteora liquidity dynamic pool"
    },

    # Pump.fun
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": {
        "name": "Pump.fun Bonding Curve",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Pump.fun automated bonding curve vault"
    },
    "Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1": {
        "name": "Pump.fun Vault",
        "category": "DEX",
        "exclude_from_concentration": True,
        "description": "Pump.fun protocol fee / escrow account"
    },

    # -------------------------------------------------------------
    # 3. PROTOCOL & BURN ADDRESSES
    # -------------------------------------------------------------
    "1nc1nerator11111111111111111111111111111111": {
        "name": "Solana Incinerator (Burn)",
        "category": "BURN",
        "exclude_from_concentration": True,
        "description": "Canonical Solana burn address"
    },
    "11111111111111111111111111111111": {
        "name": "Solana System Program",
        "category": "SYSTEM",
        "exclude_from_concentration": True,
        "description": "Solana native system program"
    }
}

def identify_known_address(address: str) -> Optional[Dict[str, Any]]:
    """
    Looks up an address in the known registry.
    Returns entity metadata if matched, or None if it's an unverified individual wallet.
    """
    if not address:
        return None
    return KNOWN_ADDRESSES.get(address)
