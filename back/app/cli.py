"""Commandes d'administration, à lancer depuis back/ :

    python -m app.cli create-admin <email> <username>   # demande le mot de passe
    python -m app.cli invite [email]                    # affiche un code d'invitation
    python -m app.cli sync                              # synchronise les humoristes suivis (cron / timer)
"""

import getpass
import sys
from datetime import timedelta

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Invitation, User, utcnow
from app.security import hash_password, new_invite_code


def create_admin(email: str, username: str) -> None:
    password = getpass.getpass("Mot de passe : ")
    if len(password) < 8:
        sys.exit("Mot de passe trop court (8 caractères minimum)")
    with SessionLocal() as db:
        if db.scalar(select(User).where((User.email == email.lower()) | (User.username == username))):
            sys.exit("Un compte avec cet email ou ce nom existe déjà")
        db.add(User(email=email.lower(), username=username, password_hash=hash_password(password), is_admin=True))
        db.commit()
    print(f"Admin {username} créé.")


def invite(email: str | None) -> None:
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.is_admin.is_(True)).order_by(User.id))
        inv = Invitation(
            code=new_invite_code(),
            email=email.lower() if email else None,
            created_by_id=admin.id if admin else None,
            expires_at=utcnow() + timedelta(days=get_settings().invite_ttl_days),
        )
        db.add(inv)
        db.commit()
        print(inv.code)


def sync() -> None:
    from app.services import catalog

    with SessionLocal() as db:
        for name, res in catalog.sync_all(db).items():
            detail = res if isinstance(res, str) else f"{res.discovered} nouveau(x), {res.filtered} filtré(s)"
            print(f"{name} : {detail}")


def main(argv: list[str]) -> None:
    match argv:
        case ["create-admin", email, username]:
            create_admin(email, username)
        case ["invite"]:
            invite(None)
        case ["invite", email]:
            invite(email)
        case ["sync"]:
            sync()
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
