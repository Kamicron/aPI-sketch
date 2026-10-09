import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api/domainApi'
import { useAuth } from '../auth/AuthContext'

export default function RegisterPage() {
  const { user, signIn } = useAuth()
  const [params] = useSearchParams()
  const [code, setCode] = useState(params.get('code') ?? '')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [codeState, setCodeState] = useState<'unknown' | 'valid' | 'invalid'>('unknown')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const trimmed = code.trim()
    if (trimmed.length < 6) {
      setCodeState('unknown')
      return
    }
    const timer = setTimeout(() => {
      authApi
        .checkInvitation(trimmed)
        .then((res) => {
          setCodeState(res.valid ? 'valid' : 'invalid')
          if (res.email) setEmail(res.email)
        })
        .catch(() => setCodeState('unknown'))
    }, 300)
    return () => clearTimeout(timer)
  }, [code])

  if (user) return <Navigate to="/" replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      signIn(await authApi.register({ code: code.trim(), email, username, password }))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1 className="brand">aPI-sketch</h1>
        <p className="muted">Crée ton compte avec ton code d'invitation.</p>
        <label>
          Code d'invitation
          <input value={code} onChange={(e) => setCode(e.target.value)} required />
          {codeState === 'valid' && <span className="hint ok">Invitation valide</span>}
          {codeState === 'invalid' && <span className="hint ko">Invitation invalide ou expirée</span>}
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
        </label>
        <label>
          Nom d'utilisateur
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            minLength={3}
            maxLength={40}
            pattern="[A-Za-z0-9_.\-]+"
            title="Lettres, chiffres, point, tiret ou underscore"
            required
          />
        </label>
        <label>
          Mot de passe
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn-primary" disabled={busy || codeState === 'invalid'}>
          {busy ? 'Création…' : 'Créer mon compte'}
        </button>
        <p className="muted small">
          Déjà inscrit ? <Link to="/login">Se connecter</Link>
        </p>
      </form>
    </div>
  )
}
