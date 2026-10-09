"""Accès à YouTube : résolution d'une chaîne (yt-dlp), flux RSS, durée d'une vidéo.

Isolé ici pour que le reste du code (et les tests) n'appelle jamais le réseau directement.
Rien n'est téléchargé : seules les métadonnées sont lues.
"""

import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import yt_dlp

FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


class YouTubeError(Exception):
    pass


@dataclass(frozen=True)
class ChannelInfo:
    channel_id: str
    name: str
    url: str


@dataclass(frozen=True)
class FeedEntry:
    video_id: str
    title: str
    published_at: datetime  # UTC, sans fuseau (comme la base)
    thumbnail_url: str | None
    description: str | None


def _ydl(**opts) -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, **opts})


def resolve_channel(url: str) -> ChannelInfo:
    """Accepte https://www.youtube.com/@handle ou /channel/UC… ; refuse tout autre site."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ALLOWED_HOSTS:
        raise YouTubeError("L'adresse doit être une chaîne YouTube")
    try:
        with _ydl(extract_flat=True, playlist_items="1") as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise YouTubeError("Chaîne introuvable") from exc
    channel_id = info.get("channel_id") or info.get("uploader_id")
    name = info.get("channel") or info.get("uploader") or info.get("title")
    if not channel_id or not str(channel_id).startswith("UC") or not name:
        raise YouTubeError("Impossible d'identifier la chaîne")
    return ChannelInfo(
        channel_id=channel_id,
        name=name,
        url=info.get("channel_url") or f"https://www.youtube.com/channel/{channel_id}",
    )


def fetch_feed(channel_id: str) -> list[FeedEntry]:
    """Les ~15 dernières vidéos de la chaîne, via le flux RSS public (pas de clé d'API)."""
    req = urllib.request.Request(FEED_URL.format(channel_id), headers={"User-Agent": "aPI-sketch"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            root = ET.fromstring(res.read())
    except (OSError, ET.ParseError) as exc:
        raise YouTubeError("Flux RSS indisponible") from exc
    entries = []
    for e in root.findall("a:entry", _NS):
        published = datetime.fromisoformat(e.findtext("a:published", namespaces=_NS))
        thumb = e.find("media:group/media:thumbnail", _NS)
        entries.append(
            FeedEntry(
                video_id=e.findtext("yt:videoId", namespaces=_NS),
                title=e.findtext("a:title", namespaces=_NS) or "",
                published_at=published.astimezone(timezone.utc).replace(tzinfo=None),
                thumbnail_url=thumb.get("url") if thumb is not None else None,
                description=e.findtext("media:group/media:description", namespaces=_NS),
            )
        )
    return entries


def video_duration(video_id: str) -> int | None:
    """Durée en secondes, ou None (direct en cours, vidéo privée/indisponible)."""
    try:
        with _ydl() as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
    except yt_dlp.utils.DownloadError:
        return None
    if info.get("is_live"):
        return None
    duration = info.get("duration")
    return int(duration) if duration else None


@dataclass(frozen=True)
class ListedVideo:
    video_id: str
    title: str
    duration_s: int | None


@dataclass(frozen=True)
class VideoDetails:
    video_id: str
    title: str
    description: str | None
    duration_s: int | None
    published_at: datetime  # UTC, sans fuseau
    thumbnail_url: str | None


def list_channel_videos(channel_id: str, limit: int) -> list[ListedVideo]:
    """Les `limit` dernières vidéos de la chaîne, du plus récent au plus ancien, avec leur durée.

    Une seule requête (listing « à plat ») : rapide, mais sans date de publication.
    """
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    try:
        with _ydl(extract_flat=True, playlist_items=f"1-{limit}") as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise YouTubeError("Liste des vidéos indisponible") from exc
    videos = []
    for e in info.get("entries") or []:
        if e.get("id") and e.get("title"):
            duration = e.get("duration")
            videos.append(ListedVideo(e["id"], e["title"], int(duration) if duration else None))
    return videos


def video_details(video_id: str) -> VideoDetails | None:
    """Métadonnées complètes d'une vidéo (None : direct, privée, indisponible ou sans date)."""
    try:
        with _ydl() as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
    except yt_dlp.utils.DownloadError:
        return None
    if info.get("is_live") or info.get("live_status") not in (None, "not_live", "was_live"):
        return None
    timestamp = info.get("timestamp")
    if timestamp:
        published = datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None)
    elif info.get("upload_date"):
        published = datetime.strptime(info["upload_date"], "%Y%m%d")
    else:
        return None
    duration = info.get("duration")
    return VideoDetails(
        video_id=video_id,
        title=info.get("title") or "",
        description=info.get("description"),
        duration_s=int(duration) if duration else None,
        published_at=published,
        thumbnail_url=info.get("thumbnail"),
    )
