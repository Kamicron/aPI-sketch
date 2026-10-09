from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import admin_user, current_user
from app.models import Comedian, Sketch, User
from app.schemas import ComedianCreate, ComedianOut, ComedianUpdate, SketchOut, SyncOut
from app.services import catalog, youtube
from app.services.library import serialize

# Lecture : tout membre. Gestion des humoristes et synchronisation : admin.
router = APIRouter(prefix="/api", tags=["catalog"])


def _out(db: Session, comedian: Comedian) -> ComedianOut:
    count = db.scalar(
        select(func.count()).select_from(Sketch).where(
            Sketch.comedian_id == comedian.id, Sketch.status == catalog.DISCOVERED
        )
    )
    return ComedianOut.model_validate(comedian).model_copy(update={"sketch_count": count or 0})


def _get(db: Session, comedian_id: int) -> Comedian:
    comedian = db.get(Comedian, comedian_id)
    if comedian is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Humoriste introuvable")
    return comedian


def _check_range(min_s: int, max_s: int) -> None:
    if min_s > max_s:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La durée minimale dépasse la durée maximale")


@router.get("/comedians", response_model=list[ComedianOut])
def list_comedians(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return [_out(db, c) for c in db.scalars(select(Comedian).order_by(Comedian.name))]


@router.post("/comedians", response_model=ComedianOut, status_code=status.HTTP_201_CREATED)
def add_comedian(body: ComedianCreate, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    _check_range(body.min_duration_s, body.max_duration_s)
    try:
        info = youtube.resolve_channel(body.channel_url)
    except youtube.YouTubeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    comedian = Comedian(
        name=info.name,
        youtube_channel_id=info.channel_id,
        channel_url=info.url,
        min_duration_s=body.min_duration_s,
        max_duration_s=body.max_duration_s,
    )
    db.add(comedian)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette chaîne est déjà suivie")
    return _out(db, comedian)


@router.patch("/comedians/{comedian_id}", response_model=ComedianOut)
def update_comedian(
    comedian_id: int, body: ComedianUpdate, _: User = Depends(admin_user), db: Session = Depends(get_db)
):
    comedian = _get(db, comedian_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(comedian, field, value)
    _check_range(comedian.min_duration_s, comedian.max_duration_s)
    db.commit()
    return _out(db, comedian)


@router.delete("/comedians/{comedian_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comedian(comedian_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    db.delete(_get(db, comedian_id))
    db.commit()


@router.post("/comedians/{comedian_id}/sync", response_model=SyncOut)
def sync_comedian(comedian_id: int, _: User = Depends(admin_user), db: Session = Depends(get_db)):
    comedian = _get(db, comedian_id)
    try:
        result = catalog.sync_comedian(db, comedian)
    except youtube.YouTubeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    return SyncOut(discovered=result.discovered, filtered=result.filtered)


@router.get("/sketches", response_model=list[SketchOut])
def list_sketches(
    comedian_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(Sketch)
        .where(Sketch.status == catalog.DISCOVERED)
        .order_by(Sketch.published_at.desc(), Sketch.id.desc())
        .limit(min(max(limit, 1), 200))
        .offset(max(offset, 0))
    )
    if comedian_id is not None:
        query = query.where(Sketch.comedian_id == comedian_id)
    return serialize(db, user, db.scalars(query).all())
