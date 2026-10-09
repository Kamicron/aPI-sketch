import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { authApi } from '../api/domainApi'
import { useAuth } from '../auth/AuthContext'

export default function LoginPage() {
  const { user, signIn } = useAuth()
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      signIn(await authApi.login(login, password))
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
        <p className="muted">Connecte-toi pour retrouver tes humoristes.</p>
        <label>
          Email ou nom d'utilisateur
          <input value={login} onChange={(e) => setLogin(e.target.value)} autoComplete="username" required />
        </label>
        <label>
          Mot de passe
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn-primary" disabled={busy}>
          {busy ? 'Connexion…' : 'Se connecter'}
        </button>
        <p className="muted small">
          Pas de compte ? L'inscription se fait sur invitation. <Link to="/register">J'ai un code</Link>
        </p>
      </form>
    </div>
  )
}
