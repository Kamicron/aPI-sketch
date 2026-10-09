import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Layout() {
  const { user, signOut } = useAuth()
  return (
    <div className="shell">
      <aside className="sidenav">
        <div className="brand">aPI-sketch</div>
        <nav>
          <NavLink to="/" end>
            Accueil
          </NavLink>
          <NavLink to="/invitations">Invitations</NavLink>
        </nav>
        <div className="sidenav-footer">
          <span className="muted small">{user?.username}</span>
          <button className="btn-ghost" onClick={signOut}>
            Déconnexion
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
