import { useEffect, useState, type FormEvent } from 'react'
import { invitationsApi } from '../api/domainApi'
import type { Invitation, InvitationStatus } from '../api/types'

const STATUS_LABEL: Record<InvitationStatus, string> = {
  pending: 'En attente',
  used: 'Utilisée',
  expired: 'Expirée',
  revoked: 'Révoquée',
}

function inviteLink(code: string) {
  return `${window.location.origin}/register?code=${encodeURIComponent(code)}`
}

export default function InvitationsPage() {
  const [items, setItems] = useState<Invitation[]>([])
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<number | null>(null)

  const reload = () => invitationsApi.list().then(setItems).catch((e) => setError(e.message))

  useEffect(() => {
    reload()
  }, [])

  async function create(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await invitationsApi.create(email.trim() || undefined)
      setEmail('')
      reload()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function copy(inv: Invitation) {
    await navigator.clipboard.writeText(inviteLink(inv.code))
    setCopied(inv.id)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <section>
      <h1>Invitations</h1>
      <p className="muted">Les comptes se créent uniquement avec un lien d'invitation (usage unique).</p>
      <form className="inline-form" onSubmit={create}>
        <input
          type="email"
          placeholder="Email du destinataire (optionnel)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button className="btn-primary">Créer une invitation</button>
      </form>
      {error && <p className="error">{error}</p>}
      <ul className="list">
        {items.map((inv) => (
          <li key={inv.id} className="list-row">
            <div>
              <code>{inv.code}</code>
              <div className="muted small">
                {inv.email ?? 'Toute adresse'} · expire le {new Date(inv.expires_at + 'Z').toLocaleDateString('fr-FR')}
              </div>
            </div>
            <span className={`badge badge-${inv.status}`}>{STATUS_LABEL[inv.status]}</span>
            {inv.status === 'pending' && (
              <div className="row-actions">
                <button className="btn-ghost" onClick={() => copy(inv)}>
                  {copied === inv.id ? 'Copié' : 'Copier le lien'}
                </button>
                <button className="btn-ghost" onClick={() => invitationsApi.revoke(inv.id).then(reload)}>
                  Révoquer
                </button>
              </div>
            )}
          </li>
        ))}
        {items.length === 0 && <li className="muted">Aucune invitation pour l'instant.</li>}
      </ul>
    </section>
  )
}
