import 'server-only'
import { cookies } from 'next/headers'
import type { User, SupabaseClient } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'

export const IMPERSONATE_COOKIE = 'pixra_impersonate_user_id'

export type UserRole = 'customer' | 'agency' | 'admin'

export interface EffectiveUser {
  user: User
  role: UserRole
  db: SupabaseClient
  impersonation: {
    adminId: string
    adminEmail: string | null
    targetId: string
    targetEmail: string | null
  } | null
}

export async function getEffectiveUser(): Promise<EffectiveUser | null> {
  const supabase = await createClient()
  const { data: { user: realUser } } = await supabase.auth.getUser()
  if (!realUser) return null

  const realRole = (realUser.user_metadata?.role as UserRole) || 'customer'
  const cookieStore = await cookies()
  const targetId = cookieStore.get(IMPERSONATE_COOKIE)?.value

  if (targetId && realRole === 'admin' && targetId !== realUser.id) {
    try {
      const admin = createAdminClient()
      const { data, error } = await admin.auth.admin.getUserById(targetId)
      if (!error && data?.user) {
        const target = data.user
        const targetRole = (target.user_metadata?.role as UserRole) || 'customer'
        return {
          user: target,
          role: targetRole,
          db: admin,
          impersonation: {
            adminId: realUser.id,
            adminEmail: realUser.email ?? null,
            targetId: target.id,
            targetEmail: target.email ?? null,
          },
        }
      }
    } catch {
      // fall through to real user
    }
  }

  return { user: realUser, role: realRole, db: supabase, impersonation: null }
}

export async function assertNotImpersonating(): Promise<void> {
  const eff = await getEffectiveUser()
  if (eff?.impersonation) {
    throw new Error('Bu işlem impersonate modunda yapılamaz — önce çıkış yap.')
  }
}
