"""Découverte : lit le flux d'un humoriste, applique le filtre de durée, enregistre les nouveautés."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Comedian, Sketch, utcnow
from app.services import youtube

DISCOVERED = "discovered"  # à proposer à l'écoute / à la découverte
FILTERED = "filtered"      # hors filtre de durée : mémorisé pour ne pas le réexaminer


@dataclass
class SyncResult:
    discovered: int = 0
    filtered: int = 0


def sync_comedian(db: Session, comedian: Comedian) -> SyncResult:
    result = SyncResult()
    entries = youtube.fetch_feed(comedian.youtube_channel_id)
    known = set(db.scalars(select(Sketch.youtube_id).where(Sketch.youtube_id.in_([e.video_id for e in entries]))))
    for entry in entries:
        if entry.video_id in known:
            continue
        duration = youtube.video_duration(entry.video_id)
        in_range = duration is not None and comedian.min_duration_s <= duration <= comedian.max_duration_s
        db.add(
            Sketch(
                comedian_id=comedian.id,
                youtube_id=entry.video_id,
                title=entry.title[:300],
                description=(entry.description or "")[:5000] or None,
                duration_s=duration,
                published_at=entry.published_at,
                thumbnail_url=entry.thumbnail_url,
                status=DISCOVERED if in_range else FILTERED,
            )
        )
        if in_range:
            result.discovered += 1
        else:
            result.filtered += 1
    comedian.last_synced_at = utcnow()
    db.commit()
    return result


def sync_all(db: Session) -> dict[str, SyncResult | str]:
    """Tous les humoristes suivis ; une chaîne en panne n'arrête pas les autres."""
    out: dict[str, SyncResult | str] = {}
    for comedian in db.scalars(select(Comedian).where(Comedian.subscribed.is_(True)).order_by(Comedian.name)):
        try:
            out[comedian.name] = sync_comedian(db, comedian)
        except youtube.YouTubeError as exc:
            db.rollback()
            out[comedian.name] = str(exc)
    return out
