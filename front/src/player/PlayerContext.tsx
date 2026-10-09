import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { libraryApi } from '../api/domainApi'
import type { Sketch } from '../api/types'

interface PlayerState {
  current: Sketch | null
  play: (sketch: Sketch) => void
  close: () => void
  isLiked: (sketch: Sketch) => boolean
  toggleLike: (sketch: Sketch) => Promise<void>
}

const PlayerContext = createContext<PlayerState | null>(null)

export function PlayerProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<Sketch | null>(null)
  // Likes modifiés pendant la session : prévaut sur l'état renvoyé par le serveur dans les listes déjà chargées.
  const [overrides, setOverrides] = useState<Record<number, boolean>>({})

  const isLiked = useCallback((s: Sketch) => overrides[s.id] ?? s.liked, [overrides])

  const toggleLike = useCallback(
    async (s: Sketch) => {
      const next = !(overrides[s.id] ?? s.liked)
      setOverrides((o) => ({ ...o, [s.id]: next }))
      try {
        await (next ? libraryApi.like(s.id) : libraryApi.unlike(s.id))
      } catch {
        setOverrides((o) => ({ ...o, [s.id]: !next }))
      }
    },
    [overrides],
  )

  const play = useCallback((s: Sketch) => {
    setCurrent(s)
    libraryApi.play(s.id).catch(() => {
      /* l'historique est secondaire : une erreur ne doit pas couper la lecture */
    })
  }, [])

  const value = useMemo(
    () => ({ current, play, close: () => setCurrent(null), isLiked, toggleLike }),
    [current, play, isLiked, toggleLike],
  )
  return <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>
}

export function usePlayer() {
  const ctx = useContext(PlayerContext)
  if (!ctx) throw new Error('usePlayer doit être utilisé dans <PlayerProvider>')
  return ctx
}
