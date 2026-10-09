"""Découverte : lit le flux d'un humoriste, applique le filtre de durée, enregistre les nouveautés."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Comedian, Sketch, utcnow
from app.services import youtube

MAX_LISTING = 1000  # plus grand nombre de vidéos d'une chaîne examinées par import d'historique
DISCOVERED ="discovered"  # à proposer à l'écoute / à la découverte
FILTERED = "filtered"      # hors filtre de durée : mémorisé pour ne pas le réexaminer


@dataclass
class SyncResult:
    discovered: int = 0
    filtered: int = 0
    remaining: int = 0  # import d'historique : sketchs retenus restant à importer (relancer)


def sync_comedian(db: Session, comedian: Comedian) -> SyncResult:
    result = SyncResult()
    entries = youtube.fetch_feed(comedian.youtube_channel_id)
    known = set(db.scalars(select(Sketch.youtube_id).where(Sketch.youtube_id.in_([e.video_id for e in entries]))))
    new_entries = [e for e in entries if e.video_id not in known]
    # Une lecture yt-dlp dure plusieurs secondes : en parallèle, pour rester sous le délai nginx.
    with ThreadPoolExecutor(max_workers=5) as pool:
        durations = list(pool.map(lambda e: youtube.video_duration(e.video_id), new_entries))
    for entry, duration in zip(new_entries, durations):
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


def backfill_comedian(db: Session, comedian: Comedian, batch: int = 100) -> SyncResult:
    """Importe l'historique de la chaîne (le flux RSS ne donne que les ~15 dernières vidéos).

    Le listing donne les durées sans les dates : on écarte d'abord, sans rien charger de plus,
    ce qui est hors filtre, puis on lit les métadonnées complètes des `batch` plus récents
    retenus. Relancer l'import continue là où il s'est arrêté (les vidéos connues sont ignorées).
    """
    listed = youtube.list_channel_videos(comedian.youtube_channel_id, MAX_LISTING)
    known = set(db.scalars(select(Sketch.youtube_id).where(Sketch.youtube_id.in_([v.video_id for v in listed]))))
    unknown = [v for v in listed if v.video_id not in known]
    candidates = [
        v for v in unknown
        if v.duration_s is not None and comedian.min_duration_s <= v.duration_s <= comedian.max_duration_s
    ]
    todo = candidates[:batch]
    with ThreadPoolExecutor(max_workers=5) as pool:
        details = list(pool.map(lambda v: youtube.video_details(v.video_id), todo))
    result = SyncResult(filtered=len(unknown) - len(candidates), remaining=len(candidates) - len(todo))
    for d in details:
        if d is None or d.duration_s is None or not comedian.min_duration_s <= d.duration_s <= comedian.max_duration_s:
            result.filtered += 1
            continue
        db.add(
            Sketch(
                comedian_id=comedian.id,
                youtube_id=d.video_id,
                title=d.title[:300],
                description=(d.description or "")[:5000] or None,
                duration_s=d.duration_s,
                published_at=d.published_at,
                thumbnail_url=d.thumbnail_url,
                status=DISCOVERED,
            )
        )
        result.discovered += 1
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
