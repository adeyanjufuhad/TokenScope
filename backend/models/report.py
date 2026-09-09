from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class FlagItem(BaseModel):
    label: str
    severity: Literal["INFO", "WARNING", "CRITICAL"]

class SecurityPillar(BaseModel):
    score: int = Field(ge=0, le=100)
    flags: List[FlagItem] = []
    mint_authority_revoked: Optional[bool] = None
    freeze_authority_revoked: Optional[bool] = None
    lp_burned_or_locked: Optional[bool] = None

class TopHolderItem(BaseModel):
    address: str
    percentage: float
    is_contract: Optional[bool] = False

class HoldersPillar(BaseModel):
    score: int = Field(ge=0, le=100)
    flags: List[FlagItem] = []
    top_holders: List[TopHolderItem] = []
    top_10_percentage: Optional[float] = None
    total_holders_count: Optional[int] = None

class MarketPillar(BaseModel):
    score: int = Field(ge=0, le=100)
    flags: List[FlagItem] = []
    liquidity_usd: float = 0.0
    volume_24h: float = 0.0
    price_usd: Optional[float] = 0.0
    market_cap_usd: Optional[float] = 0.0
    price_history: List[float] = []

class ContractPillar(BaseModel):
    score: int = Field(ge=0, le=100)
    flags: List[FlagItem] = []
    token_program: Optional[str] = "SPL Token"
    is_metadata_mutable: Optional[bool] = None

class SocialPillar(BaseModel):
    score: int = Field(ge=0, le=100)
    flags: List[FlagItem] = []
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    discord: Optional[str] = None

class PillarsContainer(BaseModel):
    security: SecurityPillar
    holders: HoldersPillar
    market: MarketPillar
    contract: ContractPillar
    social: SocialPillar

class ReportResponse(BaseModel):
    report_id: str
    mint_address: str
    token_name: str
    token_symbol: str
    generated_at: str
    overall_score: int = Field(ge=0, le=100)
    verdict: Literal["SAFE", "CAUTION", "HIGH RISK", "LIKELY RUG"]
    pillars: PillarsContainer
    ai_summary: str
    shareable_url: str

class AuditRequest(BaseModel):
    mint_address: str

class AuditInitiateResponse(BaseModel):
    report_id: str
    mint_address: str
    status: str = "completed"
    message: str = "Audit report generated successfully"
    cached: bool = False
