import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { tokenStore } from '../api/client'
import { authApi } from '../api/domainApi'
import type { TokenResponse, User } from '../api/types'

interface AuthState {
  user: User | null
  loading: boolean
  signIn: (res: TokenResponse) => void
  signOut: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => tokenStore.get() !== null)

  useEffect(() => {
    if (!tokenStore.get()) return
    authApi
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false))
  }, [])

  const signIn = useCallback((res: TokenResponse) => {
    tokenStore.set(res.access_token)
    setUser(res.user)
  }, [])

  const signOut = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  return <AuthContext.Provider value={{ user, loading, signIn, signOut }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth hors AuthProvider')
  return ctx
}
