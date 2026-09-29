from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class NonceResponse(BaseModel):
    nonce: str


class VerifySignatureRequest(BaseModel):
    wallet_address: str
    signature: str
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EscrowCreate(BaseModel):
    title: str = Field(..., max_length=140)
    description: Optional[str] = None
    terms_uri: Optional[str] = None
    receiver_address: str
    arbiter_address: Optional[str] = None
    token_address: Optional[str] = None  # None = native ETH
    amount: Decimal


class EscrowOut(BaseModel):
    id: int
    onchain_id: Optional[int]
    tx_hash: Optional[str]
    title: str
    description: Optional[str]
    sender_address: str
    receiver_address: str
    arbiter_address: Optional[str]
    token_address: Optional[str]
    amount: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EscrowConfirm(BaseModel):
    """Called by the frontend once the on-chain tx confirms, to link onchain_id + tx_hash."""
    onchain_id: int
    tx_hash: str


class DisputeCreate(BaseModel):
    escrow_id: int
    reason: str


class DisputeOut(BaseModel):
    id: int
    escrow_id: int
    raised_by: str
    reason: str
    resolution: Optional[str]
    winner_address: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenStats(BaseModel):
    token_address: str
    pair_address: Optional[str]
    price_eth: Optional[str]
    liquidity_eth: Optional[str]
    liquidity_tet: Optional[str]
    note: str = "Live figures read directly from the chain — no numbers here are simulated."
