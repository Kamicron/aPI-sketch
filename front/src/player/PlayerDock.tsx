import { usePlayer } from './PlayerContext'

// Lecteur YouTube intégré, fixé en bas : il reste affiché pendant la navigation entre les pages.
export default function PlayerDock() {
  const { current, close, isLiked, toggleLike } = usePlayer()
  if (!current) return null
  const id = encodeURIComponent(current.youtube_id)
  return (
    <div className="player-dock">
      <iframe
        key={current.youtube_id}
        title={current.title}
        src={`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`}
        allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
        allowFullScreen
      />
      <div className="player-info">
        <div className="player-text">
          <strong className="sketch-title">{current.title}</strong>
          <span className="muted small">{current.comedian_name}</span>
        </div>
        <div className="row-actions">
          <button
            className={`like-btn${isLiked(current) ? ' on' : ''}`}
            aria-label={isLiked(current) ? 'Retirer des likes' : 'Ajouter aux likes'}
            onClick={() => toggleLike(current)}
          >
            {isLiked(current) ? '♥' : '♡'}
          </button>
          <a className="btn-ghost" href={`https://www.youtube.com/watch?v=${id}`} target="_blank" rel="noopener noreferrer">
            YouTube
          </a>
          <button className="btn-ghost" onClick={close}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  )
}
