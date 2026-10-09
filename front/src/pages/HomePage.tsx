import { useAuth } from '../auth/AuthContext'

export default function HomePage() {
  const { user } = useAuth()
  return (
    <section>
      <h1>Bonjour {user?.username}</h1>
      <p className="muted">
        Tes abonnements et la découverte des humoristes arrivent à l'étape suivante.
      </p>
    </section>
  )
}
