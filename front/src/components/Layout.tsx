import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { usePlayer } from '../player/PlayerContext'
import PlayerDock from '../player/PlayerDock'

export default function Layout() {
  const { user, signOut } = useAuth()
  const { current } = usePlayer()
  return (
    <div className="shell">
      <aside className="sidenav">
        <div className="brand">aPI-sketch</div>
        <nav>
          <NavLink to="/" end>
            Accueil
          </NavLink>
          <NavLink to="/bibliotheque">Ma bibliothèque</NavLink>
          <NavLink to="/humoristes">Humoristes</NavLink>
          <NavLink to="/invitations">Invitations</NavLink>
        </nav>
        <div className="sidenav-footer">
          <span className="muted small">{user?.username}</span>
          <button className="btn-ghost" onClick={signOut}>
            Déconnexion
          </button>
        </div>
      </aside>
      <main className={`content${current ? ' has-player' : ''}`}>
        <Outlet />
      </main>
      <PlayerDock />
    </div>
  )
}
