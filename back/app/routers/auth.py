from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Invitation, User, utcnow
from app.schemas import InvitationCheck, LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    login = body.login.strip().lower()
    user = db.scalar(
        select(User).where(or_(func.lower(User.email) == login, func.lower(User.username) == login))
    )
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants incorrects")
    return _token_response(user)


def _usable_invitation(db: Session, code: str) -> Invitation | None:
    inv = db.scalar(select(Invitation).where(Invitation.code == code))
    return inv if inv is not None and inv.status == "pending" else None


@router.get("/invitations/{code}", response_model=InvitationCheck)
def check_invitation(code: str, db: Session = Depends(get_db)):
    inv = _usable_invitation(db, code)
    return InvitationCheck(valid=inv is not None, email=inv.email if inv else None)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    inv = _usable_invitation(db, body.code)
    if inv is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invitation invalide ou expirée")
    email = body.email.lower()
    if inv.email and inv.email.lower() != email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cette invitation est réservée à une autre adresse")
    if db.scalar(select(User).where(func.lower(User.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Adresse déjà utilisée")
    if db.scalar(select(User).where(func.lower(User.username) == body.username.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Nom d'utilisateur déjà pris")

    user = User(
        email=email,
        username=body.username,
        password_hash=hash_password(body.password),
        invited_by_id=inv.created_by_id,
    )
    db.add(user)
    db.flush()
    inv.used_by_id = user.id
    inv.used_at = utcnow()
    db.commit()
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
