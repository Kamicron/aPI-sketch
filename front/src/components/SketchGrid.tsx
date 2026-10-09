import type { Sketch } from '../api/types'
import { usePlayer } from '../player/PlayerContext'

export function formatDuration(seconds: number | null) {
  if (seconds == null) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = String(seconds % 60).padStart(2, '0')
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`
}

export function formatDate(iso: string | null) {
  return iso ? new Date(iso + 'Z').toLocaleDateString('fr-FR') : 'jamais'
}

export default function SketchGrid({ sketches, empty }: { sketches: Sketch[]; empty: string }) {
  const { current, play, isLiked, toggleLike } = usePlayer()
  if (sketches.length === 0) return empty ? <p className="muted">{empty}</p> : null
  return (
    <ul className="sketch-grid">
      {sketches.map((s) => (
        <li key={s.id} className={`sketch-card${current?.id === s.id ? ' playing' : ''}`}>
          <button className="sketch-play" onClick={() => play(s)}>
            <div className="thumb">
              {s.thumbnail_url && <img src={s.thumbnail_url} alt="" loading="lazy" />}
              <span className="duration">{formatDuration(s.duration_s)}</span>
            </div>
            <span className="sketch-title">{s.title}</span>
            <span className="muted small">
              {s.comedian_name} · {formatDate(s.published_at)}
            </span>
          </button>
          <button
            className={`like-btn card-like${isLiked(s) ? ' on' : ''}`}
            aria-label={isLiked(s) ? 'Retirer des likes' : 'Ajouter aux likes'}
            onClick={() => toggleLike(s)}
          >
            {isLiked(s) ? '♥' : '♡'}
          </button>
        </li>
      ))}
    </ul>
  )
}
