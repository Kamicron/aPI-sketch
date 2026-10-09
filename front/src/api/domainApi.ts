import { api } from './client'
import type { Invitation, TokenResponse, User } from './types'

export const authApi = {
  login: (login: string, password: string) =>
    api<TokenResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ login, password }) }),
  register: (body: { code: string; email: string; username: string; password: string }) =>
    api<TokenResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }),
  checkInvitation: (code: string) =>
    api<{ valid: boolean; email: string | null }>(`/api/auth/invitations/${encodeURIComponent(code)}`),
  me: () => api<User>('/api/auth/me'),
}

export const invitationsApi = {
  list: () => api<Invitation[]>('/api/invitations'),
  create: (email?: string) =>
    api<Invitation>('/api/invitations', { method: 'POST', body: JSON.stringify({ email: email || null }) }),
  revoke: (id: number) => api<void>(`/api/invitations/${id}`, { method: 'DELETE' }),
}
