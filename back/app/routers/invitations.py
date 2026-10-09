from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import current_user
from app.models import Invitation, User, utcnow
from app.schemas import InvitationCreate, InvitationOut
from app.security import new_invite_code

# Tout membre peut inviter ; un admin voit et révoque toutes les invitations.
router = APIRouter(prefix="/api/invitations", tags=["invitations"])


@router.get("", response_model=list[InvitationOut])
def list_invitations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Invitation).order_by(Invitation.created_at.desc())
    if not user.is_admin:
        query = query.where(Invitation.created_by_id == user.id)
    return db.scalars(query).all()


@router.post("", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
def create_invitation(
    body: InvitationCreate, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    ttl = body.ttl_days or get_settings().invite_ttl_days
    inv = Invitation(
        code=new_invite_code(),
        email=body.email.lower() if body.email else None,
        created_by_id=user.id,
        expires_at=utcnow() + timedelta(days=ttl),
    )
    db.add(inv)
    db.commit()
    return inv


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    inv = db.get(Invitation, invitation_id)
    if inv is None or (not user.is_admin and inv.created_by_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation introuvable")
    if inv.used_at is None:
        inv.revoked = True
        db.commit()
