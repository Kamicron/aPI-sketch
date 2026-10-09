export interface User {
  id: number
  email: string
  username: string
  is_admin: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export type InvitationStatus = 'pending' | 'used' | 'expired' | 'revoked'

export interface Invitation {
  id: number
  code: string
  email: string | null
  status: InvitationStatus
  created_at: string
  expires_at: string
  used_at: string | null
}

export interface Comedian {
  id: number
  name: string
  youtube_channel_id: string
  channel_url: string
  subscribed: boolean
  min_duration_s: number
  max_duration_s: number
  last_synced_at: string | null
  sketch_count: number
}

export interface Sketch {
  id: number
  comedian_id: number
  comedian_name: string
  youtube_id: string
  title: string
  duration_s: number | null
  published_at: string
  thumbnail_url: string | null
  liked: boolean
}

export interface SyncResult {
  discovered: number
  filtered: number
}
