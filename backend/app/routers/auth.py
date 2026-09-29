import os
import secrets
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Header
from jose import jwt
from eth_account.messages import encode_defunct
from eth_account import Account
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import NonceResponse, VerifySignatureRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# In-memory nonce store — swap for Redis in production (multi-instance deployments).
_nonces: dict[str, tuple[str, float]] = {}
NONCE_TTL_SECONDS = 300


@router.get("/nonce/{wallet_address}", response_model=NonceResponse)
def get_nonce(wallet_address: str):
    nonce = secrets.token_hex(16)
    _nonces[wallet_address.lower()] = (nonce, time.time())
    return NonceResponse(nonce=nonce)


@router.post("/verify", response_model=TokenResponse)
def verify_signature(payload: VerifySignatureRequest, db: Session = Depends(get_db)):
    addr = payload.wallet_address.lower()
    entry = _nonces.get(addr)
    if not entry:
        raise HTTPException(400, "No nonce requested for this address")
    nonce, issued_at = entry
    if time.time() - issued_at > NONCE_TTL_SECONDS:
        raise HTTPException(400, "Nonce expired, request a new one")
    if nonce not in payload.message:
        raise HTTPException(400, "Nonce mismatch")

    # Verify the wallet actually signed this exact message (proves control of the private key
    # without ever touching it — this is the whole point of wallet-based auth).
    message = encode_defunct(text=payload.message)
    try:
        recovered = Account.recover_message(message, signature=payload.signature)
    except Exception:
        raise HTTPException(400, "Invalid signature")

    if recovered.lower() != addr:
        raise HTTPException(401, "Signature does not match wallet address")

    del _nonces[addr]

    user = db.query(User).filter(User.wallet_address == addr).first()
    if not user:
        user = User(wallet_address=addr)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = jwt.encode(
        {"sub": addr, "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)},
        JWT_SECRET,
        algorithm="HS256",
    )
    return TokenResponse(access_token=token)


def get_current_wallet(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    return payload["sub"]
