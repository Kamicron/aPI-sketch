from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Like, Play, Sketch, User, utcnow
from app.schemas import SketchOut
from app.services.library import playable_sketch, serialize

# Espace personnel : chaque membre ne voit et ne modifie que ses propres likes et son historique.
router = APIRouter(prefix="/api", tags=["library"])


@router.put("/sketches/{sketch_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like(sketch_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    playable_sketch(db, sketch_id)
    if db.get(Like, (user.id, sketch_id)) is None:
        db.add(Like(user_id=user.id, sketch_id=sketch_id))
        db.commit()


@router.delete("/sketches/{sketch_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike(sketch_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    existing = db.get(Like, (user.id, sketch_id))
    if existing is not None:
        db.delete(existing)
        db.commit()


@router.post("/sketches/{sketch_id}/play", status_code=status.HTTP_204_NO_CONTENT)
def record_play(sketch_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    playable_sketch(db, sketch_id)
    play = db.get(Play, (user.id, sketch_id))
    if play is None:
        db.add(Play(user_id=user.id, sketch_id=sketch_id))
    else:
        play.last_played_at = utcnow()
        play.play_count += 1
    db.commit()


@router.get("/me/likes", response_model=list[SketchOut])
def my_likes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    sketches = db.scalars(
        select(Sketch).join(Like, Like.sketch_id == Sketch.id).where(Like.user_id == user.id).order_by(Like.created_at.desc())
    ).all()
    return serialize(db, user, sketches)


@router.get("/me/history", response_model=list[SketchOut])
def my_history(limit: int = 50, user: User = Depends(current_user), db: Session = Depends(get_db)):
    sketches = db.scalars(
        select(Sketch)
        .join(Play, Play.sketch_id == Sketch.id)
        .where(Play.user_id == user.id)
        .order_by(Play.last_played_at.desc())
        .limit(min(max(limit, 1), 200))
    ).all()
    return serialize(db, user, sketches)
