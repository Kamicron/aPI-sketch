import { useEffect, useState } from 'react'
import { libraryApi } from '../api/domainApi'
import type { Sketch } from '../api/types'
import SketchGrid from '../components/SketchGrid'

type Tab = 'likes' | 'history'

export default function LibraryPage() {
  const [tab, setTab] = useState<Tab>('likes')
  const [items, setItems] = useState<Sketch[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setError(null)
    const load = tab === 'likes' ? libraryApi.likes() : libraryApi.history()
    load.then(setItems).catch((e) => setError(e.message))
  }, [tab])

  return (
    <section>
      <h1>Ma bibliothèque</h1>
      <p className="muted">
        Tes sketchs likés et ce que tu as écouté récemment. C'est personnel : les autres membres ne le voient pas.
      </p>
      <div className="chips">
        <button className={`chip${tab === 'likes' ? ' active' : ''}`} onClick={() => setTab('likes')}>
          Mes likes
        </button>
        <button className={`chip${tab === 'history' ? ' active' : ''}`} onClick={() => setTab('history')}>
          Historique
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <SketchGrid
        sketches={items}
        empty={tab === 'likes' ? 'Aucun like : clique sur ♡ sur un sketch.' : "Rien d'écouté pour l'instant."}
      />
    </section>
  )
}
