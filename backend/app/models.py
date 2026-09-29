import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, Numeric, Text, BigInteger
from .database import Base


class AgreementStatus(str, enum.Enum):
    created = "created"
    funded = "funded"
    delivered = "delivered"
    released = "released"
    disputed = "disputed"
    resolved = "resolved"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, index=True, nullable=False)
    display_name = Column(String(64), nullable=True)
    reputation_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Escrow(Base):
    """Off-chain mirror of an on-chain TetEscrow Agreement, plus UI metadata
    (title/description) that isn't worth storing on-chain."""

    __tablename__ = "escrows"
    id = Column(Integer, primary_key=True, index=True)
    onchain_id = Column(BigInteger, unique=True, index=True, nullable=True)  # null until confirmed on-chain
    tx_hash = Column(String(66), nullable=True)

    title = Column(String(140), nullable=False)
    description = Column(Text, nullable=True)
    terms_uri = Column(String(512), nullable=True)

    sender_address = Column(String(42), index=True, nullable=False)
    receiver_address = Column(String(42), index=True, nullable=False)
    arbiter_address = Column(String(42), nullable=True)

    token_address = Column(String(42), nullable=True)  # null/zero-address = native ETH
    amount = Column(Numeric(38, 18), nullable=False)

    status = Column(Enum(AgreementStatus), default=AgreementStatus.created, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(Integer, primary_key=True, index=True)
    escrow_id = Column(Integer, index=True, nullable=False)
    raised_by = Column(String(42), nullable=False)
    reason = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    winner_address = Column(String(42), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
