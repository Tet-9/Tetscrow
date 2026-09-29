from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Escrow, AgreementStatus
from ..schemas import EscrowCreate, EscrowOut, EscrowConfirm
from .auth import get_current_wallet
from ..web3_client import read_agreement_onchain

router = APIRouter(prefix="/escrows", tags=["escrows"])

STATUS_MAP = ["created", "funded", "delivered", "released", "disputed", "resolved", "cancelled"]


@router.post("", response_model=EscrowOut)
def create_escrow(payload: EscrowCreate, wallet: str = Depends(get_current_wallet), db: Session = Depends(get_db)):
    """Records the escrow's off-chain metadata (title, description) BEFORE the on-chain
    tx is sent. The frontend then submits the createAgreement() tx itself (the user's own
    wallet signs it — this backend never holds funds or private keys), and calls
    /escrows/{id}/confirm once it's mined, to attach the onchain_id + tx hash."""
    escrow = Escrow(
        title=payload.title,
        description=payload.description,
        terms_uri=payload.terms_uri,
        sender_address=wallet,
        receiver_address=payload.receiver_address.lower(),
        arbiter_address=(payload.arbiter_address or "").lower() or None,
        token_address=(payload.token_address or "").lower() or None,
        amount=payload.amount,
        status=AgreementStatus.created,
    )
    db.add(escrow)
    db.commit()
    db.refresh(escrow)
    return escrow


@router.post("/{escrow_id}/confirm", response_model=EscrowOut)
def confirm_escrow(escrow_id: int, payload: EscrowConfirm, wallet: str = Depends(get_current_wallet), db: Session = Depends(get_db)):
    escrow = db.get(Escrow, escrow_id)
    if not escrow:
        raise HTTPException(404, "Escrow not found")
    if escrow.sender_address != wallet:
        raise HTTPException(403, "Only the sender can confirm this escrow")

    escrow.onchain_id = payload.onchain_id
    escrow.tx_hash = payload.tx_hash
    db.commit()
    db.refresh(escrow)
    return escrow


@router.get("/mine", response_model=list[EscrowOut])
def my_escrows(wallet: str = Depends(get_current_wallet), db: Session = Depends(get_db)):
    return (
        db.query(Escrow)
        .filter((Escrow.sender_address == wallet) | (Escrow.receiver_address == wallet))
        .order_by(Escrow.created_at.desc())
        .all()
    )


@router.get("/{escrow_id}", response_model=EscrowOut)
def get_escrow(escrow_id: int, sync: bool = False, db: Session = Depends(get_db)):
    escrow = db.get(Escrow, escrow_id)
    if not escrow:
        raise HTTPException(404, "Escrow not found")

    if sync and escrow.onchain_id is not None:
        # Re-sync status from the contract itself, so the UI never trusts stale DB state
        # over what's actually true on-chain.
        onchain = read_agreement_onchain(escrow.onchain_id)
        escrow.status = AgreementStatus(STATUS_MAP[onchain["status"]])
        db.commit()
        db.refresh(escrow)

    return escrow
