import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { redirect } from 'next/navigation'
import { AppShell, type UserRole } from '@/components/shell/AppShell'
import AdminClient from './admin-client'

export default async function AdminPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const role = (user.user_metadata?.role as UserRole) || 'customer'
  if (role !== 'admin') redirect('/')

  const admin = createAdminClient()

  const { data: creditRow } = await supabase
    .from('credits').select('balance').eq('user_id', user.id).maybeSingle()

  // Tüm auth kullanıcıları
  const { data: { users: authUsers } } = await admin.auth.admin.listUsers({ perPage: 200 })

  // Tüm organizasyonlar + krediler + session sayıları
  const [
    { data: orgs },
    { data: allCredits },
    { data: sessionCounts },
    { data: recentSessions },
  ] = await Promise.all([
    admin.from('organizations').select('*'),
    admin.from('credits').select('user_id, balance, updated_at'),
    admin.from('ai_sessions').select('user_id, status'),
    admin.from('ai_sessions')
      .select('id, job_name, status, total_products, processed_products, created_at, completed_at, error_message, organizations(company_name)')
      .order('created_at', { ascending: false })
      .limit(20),
  ])

  const orgMap = Object.fromEntries((orgs || []).map(o => [o.user_id, o]))
  const creditMap = Object.fromEntries((allCredits || []).map(c => [c.user_id, c]))
  const sessionMap: Record<string, number> = {}
  for (const s of sessionCounts || []) {
    sessionMap[s.user_id] = (sessionMap[s.user_id] || 0) + 1
  }

  const customers = (authUsers || [])
    .filter(u => u.user_metadata?.role !== 'admin')
    .map(u => ({
      id: u.id,
      email: u.email || null,
      full_name: (u.user_metadata?.full_name as string) || null,
      created_at: u.created_at,
      last_sign_in_at: u.last_sign_in_at || null,
      org: orgMap[u.id] || null,
      credits: creditMap[u.id]?.balance ?? 0,
      session_count: sessionMap[u.id] || 0,
    }))
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  const kpis = {
    users: customers.length,
    firms: (orgs || []).length,
    sessions: (sessionCounts || []).length,
    totalCredits: (allCredits || []).reduce((s, c) => s + (c.balance || 0), 0),
  }

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 0} firmName="Pixra Admin">
      <AdminClient
        kpis={kpis}
        customers={customers}
        recentSessions={recentSessions || []}
      />
    </AppShell>
  )
}
