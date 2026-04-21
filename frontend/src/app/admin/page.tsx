import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { AppShell, type UserRole } from '@/components/shell/AppShell'
import AdminClient from './admin-client'

export default async function AdminPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const role = (user.user_metadata?.role as UserRole) || 'customer'
  if (role !== 'admin') redirect('/')

  const { data: creditRow } = await supabase
    .from('credits').select('balance').eq('user_id', user.id).maybeSingle()

  const [
    { count: totalUsers },
    { count: totalFirms },
    { count: totalSessions },
    { data: recentSessions },
    { data: topFirms },
  ] = await Promise.all([
    supabase.from('organizations').select('user_id', { count: 'exact', head: true }),
    supabase.from('organizations').select('id', { count: 'exact', head: true }),
    supabase.from('ai_sessions').select('id', { count: 'exact', head: true }),
    supabase.from('ai_sessions')
      .select('id, job_name, status, total_products, processed_products, created_at, organizations(company_name)')
      .order('created_at', { ascending: false })
      .limit(10),
    supabase.from('organizations')
      .select('id, company_name, domain_url, ws_kodu, created_at, user_id')
      .order('created_at', { ascending: false })
      .limit(50),
  ])

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 0} firmName="Pixra Admin">
      <AdminClient
        kpis={{
          users: totalUsers || 0,
          firms: totalFirms || 0,
          sessions: totalSessions || 0,
        }}
        recentSessions={recentSessions || []}
        firms={topFirms || []}
      />
    </AppShell>
  )
}
