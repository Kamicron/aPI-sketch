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
