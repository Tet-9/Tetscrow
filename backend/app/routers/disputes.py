from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Dispute, Escrow, AgreementStatus
from ..schemas import DisputeCreate, DisputeOut
from .auth import get_current_wallet

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("", response_model=DisputeOut)
def raise_dispute(payload: DisputeCreate, wallet: str = Depends(get_current_wallet), db: Session = Depends(get_db)):
    escrow = db.get(Escrow, payload.escrow_id)
    if not escrow:
        raise HTTPException(404, "Escrow not found")
    if wallet not in (escrow.sender_address, escrow.receiver_address):
        raise HTTPException(403, "Only a party to this escrow can raise a dispute")
    if escrow.status not in (AgreementStatus.funded, AgreementStatus.delivered):
        raise HTTPException(400, f"Cannot dispute an escrow in status '{escrow.status}'")

    dispute = Dispute(escrow_id=escrow.id, raised_by=wallet, reason=payload.reason)
    db.add(dispute)
    escrow.status = AgreementStatus.disputed
    db.commit()
    db.refresh(dispute)
    return dispute


@router.get("/{escrow_id}", response_model=list[DisputeOut])
def get_disputes_for_escrow(escrow_id: int, db: Session = Depends(get_db)):
    return db.query(Dispute).filter(Dispute.escrow_id == escrow_id).order_by(Dispute.created_at.desc()).all()


@router.post("/{dispute_id}/resolve", response_model=DisputeOut)
def resolve_dispute(dispute_id: int, winner_address: str, resolution: str, wallet: str = Depends(get_current_wallet), db: Session = Depends(get_db)):
    """Records the arbiter's off-chain resolution note. The actual fund release still
    happens by the arbiter calling resolveDispute() on-chain directly — this endpoint
    just keeps a human-readable record of *why*, for transparency and support history."""
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(404, "Dispute not found")
    escrow = db.get(Escrow, dispute.escrow_id)
    if escrow.arbiter_address and wallet != escrow.arbiter_address:
        raise HTTPException(403, "Only the assigned arbiter can resolve this dispute")

    dispute.resolution = resolution
    dispute.winner_address = winner_address.lower()
    dispute.resolved_at = datetime.utcnow()
    escrow.status = AgreementStatus.resolved
    db.commit()
    db.refresh(dispute)
    return dispute
