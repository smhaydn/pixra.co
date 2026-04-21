'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { IMPERSONATE_COOKIE } from '@/lib/auth/effective-user'

async function assertAdmin() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')
  const role = user.user_metadata?.role
  if (role !== 'admin') {
    throw new Error('Forbidden: admin required')
  }
  return user
}

export async function startImpersonate(targetUserId: string) {
  await assertAdmin()
  const cookieStore = await cookies()
  cookieStore.set(IMPERSONATE_COOKIE, targetUserId, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 2, // 2 saat
  })
  redirect('/')
}

export async function exitImpersonate() {
  const cookieStore = await cookies()
  cookieStore.delete(IMPERSONATE_COOKIE)
  redirect('/admin')
}

export async function adjustCredits(targetUserId: string, delta: number, note: string) {
  await assertAdmin()
  if (!Number.isFinite(delta) || delta === 0) {
    throw new Error('Geçerli bir miktar gir')
  }
  const admin = createAdminClient()

  const { data: existing } = await admin
    .from('credits')
    .select('balance')
    .eq('user_id', targetUserId)
    .maybeSingle()

  const current = existing?.balance ?? 0
  const newBalance = Math.max(0, current + delta)

  if (existing) {
    await admin.from('credits').update({ balance: newBalance }).eq('user_id', targetUserId)
  } else {
    await admin.from('credits').insert({ user_id: targetUserId, balance: newBalance })
  }

  await admin.from('credit_adjustments').insert({
    user_id: targetUserId,
    delta,
    balance_after: newBalance,
    note,
  })

  revalidatePath(`/admin/customers/${targetUserId}`)
}
