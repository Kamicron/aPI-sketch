import { api } from './client'
import type { Comedian, Invitation, Sketch, SyncResult, TokenResponse, User } from './types'

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

export const catalogApi = {
  comedians: () => api<Comedian[]>('/api/comedians'),
  addComedian: (body: { channel_url: string; min_duration_s: number; max_duration_s: number }) =>
    api<Comedian>('/api/comedians', { method: 'POST', body: JSON.stringify(body) }),
  updateComedian: (id: number, body: Partial<Pick<Comedian, 'subscribed' | 'min_duration_s' | 'max_duration_s'>>) =>
    api<Comedian>(`/api/comedians/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteComedian: (id: number) => api<void>(`/api/comedians/${id}`, { method: 'DELETE' }),
  sync: (id: number) => api<SyncResult>(`/api/comedians/${id}/sync`, { method: 'POST' }),
  backfill: (id: number) => api<SyncResult>(`/api/comedians/${id}/backfill?batch=100`, { method: 'POST' }),
  sketches: (comedianId?: number, limit = 100) =>
    api<Sketch[]>(`/api/sketches?limit=${limit}${comedianId ? `&comedian_id=${comedianId}` : ''}`),
}

export const libraryApi = {
  like: (id: number) => api<void>(`/api/sketches/${id}/like`, { method: 'PUT' }),
  unlike: (id: number) => api<void>(`/api/sketches/${id}/like`, { method: 'DELETE' }),
  play: (id: number) => api<void>(`/api/sketches/${id}/play`, { method: 'POST' }),
  likes: () => api<Sketch[]>('/api/me/likes'),
  history: (limit = 50) => api<Sketch[]>(`/api/me/history?limit=${limit}`),
}
