"""Sérialisation des sketchs pour un membre (état « liké ») et accès aux sketchs écoutables."""

from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Like, Sketch, User
from app.schemas import SketchOut
from app.services.catalog import DISCOVERED


def serialize(db: Session, user: User, sketches: Sequence[Sketch]) -> list[SketchOut]:
    liked = set(db.scalars(select(Like.sketch_id).where(Like.user_id == user.id, Like.sketch_id.in_([s.id for s in sketches]))))
    return [
        SketchOut.model_validate(s).model_copy(update={"comedian_name": s.comedian.name, "liked": s.id in liked})
        for s in sketches
    ]


def playable_sketch(db: Session, sketch_id: int) -> Sketch:
    sketch = db.get(Sketch, sketch_id)
    if sketch is None or sketch.status != DISCOVERED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sketch introuvable")
    return sketch
