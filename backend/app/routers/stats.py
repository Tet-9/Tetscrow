from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Escrow, AgreementStatus

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def platform_stats(db: Session = Depends(get_db)):
    """Real counts straight from the database, so the numbers shown to visitors are true."""
    users = db.query(func.count(User.id)).scalar() or 0
    agreements = db.query(func.count(Escrow.id)).scalar() or 0
    released = (
        db.query(func.coalesce(func.sum(Escrow.amount), 0))
        .filter(Escrow.status.in_([AgreementStatus.released, AgreementStatus.resolved]), Escrow.token_address.is_(None))
        .scalar()
    )
    return {"users_registered": users, "agreements_created": agreements, "funds_released_eth": str(released or 0)}
