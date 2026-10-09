import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { catalogApi } from '../api/domainApi'
import type { Comedian, Sketch } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import SketchGrid, { formatDate } from '../components/SketchGrid'

export default function ComediansPage() {
  const { user } = useAuth()
  const isAdmin = !!user?.is_admin

  const [comedians, setComedians] = useState<Comedian[]>([])
  const [sketches, setSketches] = useState<Sketch[]>([])
  const [selected, setSelected] = useState<number | undefined>()
  const [url, setUrl] = useState('')
  const [minMin, setMinMin] = useState('2')
  const [maxMin, setMaxMin] = useState('30')
  const [busy, setBusy] = useState<number | 'add' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)

  const loadComedians = useCallback(
    () => catalogApi.comedians().then(setComedians).catch((e) => setError(e.message)),
    [],
  )
  const loadSketches = useCallback(
    () => catalogApi.sketches(selected).then(setSketches).catch((e) => setError(e.message)),
    [selected],
  )

  useEffect(() => {
    loadComedians()
  }, [loadComedians])
  useEffect(() => {
    loadSketches()
  }, [loadSketches])

  async function run(key: number | 'add', action: () => Promise<void>) {
    setBusy(key)
    setError(null)
    setInfo(null)
    try {
      await action()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(null)
    }
  }

  function add(e: FormEvent) {
    e.preventDefault()
    run('add', async () => {
      const created = await catalogApi.addComedian({
        channel_url: url.trim(),
        min_duration_s: Math.round(Number(minMin) * 60),
        max_duration_s: Math.round(Number(maxMin) * 60),
      })
      setUrl('')
      setInfo(`${created.name} ajouté. Lance une synchronisation pour récupérer ses sketchs.`)
      await loadComedians()
    })
  }

  const sync = (c: Comedian) =>
    run(c.id, async () => {
      const r = await catalogApi.sync(c.id)
      setInfo(`${c.name} : ${r.discovered} nouveau(x), ${r.filtered} écarté(s) par le filtre de durée.`)
      await Promise.all([loadComedians(), loadSketches()])
    })

  const backfill = (c: Comedian) =>
    run(c.id, async () => {
      // Lots de 100 enchaînés jusqu'à épuisement (chaque appel reste sous le délai nginx).
      let imported = 0
      for (;;) {
        const r = await catalogApi.backfill(c.id)
        imported += r.discovered
        await Promise.all([loadComedians(), loadSketches()])
        if (r.remaining === 0) {
          setInfo(`${c.name} : ${imported} sketch(s) importé(s). L'historique est complet.`)
          break
        }
        if (r.discovered === 0) {
          setInfo(`${c.name} : import interrompu (${imported} importé(s), encore ${r.remaining}). Réessaie plus tard.`)
          break
        }
        setInfo(`${c.name} : ${imported} importé(s), encore ${r.remaining} à venir… (ne ferme pas la page)`)
      }
    })

  const toggle = (c: Comedian) =>
    run(c.id, async () => {
      await catalogApi.updateComedian(c.id, { subscribed: !c.subscribed })
      await loadComedians()
    })

  const remove = (c: Comedian) => {
    if (!window.confirm(`Supprimer ${c.name} et ses ${c.sketch_count} sketch(s) ?`)) return
    run(c.id, async () => {
      await catalogApi.deleteComedian(c.id)
      if (selected === c.id) setSelected(undefined)
      await Promise.all([loadComedians(), loadSketches()])
    })
  }

  return (
    <section>
      <h1>Humoristes</h1>
      <p className="muted">
        Les chaînes YouTube suivies. Seuls les sketchs dont la durée est dans le filtre sont retenus.
      </p>

      {isAdmin && (
        <form className="inline-form" onSubmit={add}>
          <input
            type="url"
            required
            placeholder="https://www.youtube.com/@humoriste"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <input
            className="narrow"
            type="number"
            min="0"
            title="Durée minimale (minutes)"
            aria-label="Durée minimale en minutes"
            value={minMin}
            onChange={(e) => setMinMin(e.target.value)}
          />
          <input
            className="narrow"
            type="number"
            min="1"
            title="Durée maximale (minutes)"
            aria-label="Durée maximale en minutes"
            value={maxMin}
            onChange={(e) => setMaxMin(e.target.value)}
          />
          <button className="btn-primary" disabled={busy === 'add'}>
            {busy === 'add' ? 'Ajout…' : 'Ajouter'}
          </button>
        </form>
      )}
      {error && <p className="error">{error}</p>}
      {info && <p className="muted">{info}</p>}

      <ul className="list">
        {comedians.map((c) => (
          <li key={c.id} className={`list-row comedian-row${c.subscribed ? '' : ' off'}`}>
            <div>
              <strong>{c.name}</strong>
              <div className="muted small">
                {c.sketch_count} sketch(s) · {Math.round(c.min_duration_s / 60)}–{Math.round(c.max_duration_s / 60)} min ·
                synchro : {formatDate(c.last_synced_at)}
              </div>
            </div>
            {!c.subscribed && <span className="badge">En pause</span>}
            {isAdmin && (
              <div className="row-actions">
                <button className="btn-ghost" disabled={busy === c.id} onClick={() => sync(c)}>
                  {busy === c.id ? 'Synchro…' : 'Synchroniser'}
                </button>
                <button className="btn-ghost" disabled={busy === c.id} onClick={() => backfill(c)}>
                  Importer l'historique
                </button>
                <button className="btn-ghost" disabled={busy === c.id} onClick={() => toggle(c)}>
                  {c.subscribed ? 'Mettre en pause' : 'Reprendre'}
                </button>
                <button className="btn-ghost" disabled={busy === c.id} onClick={() => remove(c)}>
                  Supprimer
                </button>
              </div>
            )}
          </li>
        ))}
        {comedians.length === 0 && (
          <li className="muted">
            Aucun humoriste pour l'instant{isAdmin ? ' : colle l\'adresse d\'une chaîne ci-dessus.' : '.'}
          </li>
        )}
      </ul>

      <h2 className="section-title">Sketchs</h2>
      <div className="chips">
        <button className={`chip${selected === undefined ? ' active' : ''}`} onClick={() => setSelected(undefined)}>
          Tous
        </button>
        {comedians.map((c) => (
          <button
            key={c.id}
            className={`chip${selected === c.id ? ' active' : ''}`}
            onClick={() => setSelected(c.id)}
          >
            {c.name}
          </button>
        ))}
      </div>
      <SketchGrid sketches={sketches} empty="Aucun sketch pour l'instant." />
    </section>
  )
}
