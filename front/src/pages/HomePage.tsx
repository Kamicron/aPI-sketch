import { useEffect, useState } from 'react'
import { catalogApi, libraryApi } from '../api/domainApi'
import type { Sketch } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import SketchGrid from '../components/SketchGrid'

export default function HomePage() {
  const { user } = useAuth()
  const [recent, setRecent] = useState<Sketch[]>([])
  const [latest, setLatest] = useState<Sketch[]>([])

  useEffect(() => {
    libraryApi.history(8).then(setRecent).catch(() => {})
    catalogApi.sketches(undefined, 8).then(setLatest).catch(() => {})
  }, [])

  return (
    <section>
      <h1>Bonjour {user?.username}</h1>
      {recent.length > 0 && (
        <>
          <h2 className="section-title">Écoutés récemment</h2>
          <SketchGrid sketches={recent} empty="" />
        </>
      )}
      <h2 className="section-title">Nouveautés</h2>
      <SketchGrid sketches={latest} empty="Aucun sketch pour l'instant : l'admin peut ajouter des humoristes." />
    </section>
  )
}
