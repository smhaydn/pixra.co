import { redirect, notFound } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { AppShell, type UserRole } from '@/components/shell/AppShell'
import CustomerDetailClient from './customer-detail-client'

export default async function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: targetId } = await params

  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const role = (user.user_metadata?.role as UserRole) || 'customer'
  if (role !== 'admin') redirect('/')

  const admin = createAdminClient()

  const { data: authData, error: authError } = await admin.auth.admin.getUserById(targetId)
  if (authError || !authData?.user) notFound()
  const target = authData.user

  const [
    { data: firm },
    { data: creditRow },
    { data: sessions },
    { data: adjustments },
  ] = await Promise.all([
    admin.from('organizations').select('*').eq('user_id', targetId).maybeSingle(),
    admin.from('credits').select('balance, updated_at').eq('user_id', targetId).maybeSingle(),
    admin.from('ai_sessions')
      .select('id, job_name, status, total_products, processed_products, created_at')
      .eq('user_id', targetId)
      .order('created_at', { ascending: false })
      .limit(20),
    admin.from('credit_adjustments')
      .select('id, delta, balance_after, note, created_at')
      .eq('user_id', targetId)
      .order('created_at', { ascending: false })
      .limit(10),
  ])

  const { data: adminCredits } = await supabase
    .from('credits').select('balance').eq('user_id', user.id).maybeSingle()

  return (
    <AppShell user={user} role={role} credits={adminCredits?.balance ?? 0} firmName="Pixra Admin">
      <div style={{ marginBottom: 16, fontSize: 'var(--text-sm)' }}>
        <Link href="/admin" style={{ color: 'var(--text-tertiary)', textDecoration: 'none' }}>← Admin</Link>
      </div>
      <CustomerDetailClient
        target={{
          id: target.id,
          email: target.email || null,
          created_at: target.created_at,
          last_sign_in_at: target.last_sign_in_at || null,
          full_name: (target.user_metadata?.full_name as string) || null,
          role: (target.user_metadata?.role as string) || 'customer',
        }}
        firm={firm}
        credits={creditRow?.balance ?? 0}
        creditsUpdatedAt={creditRow?.updated_at || null}
        sessions={sessions || []}
        adjustments={adjustments || []}
      />
    </AppShell>
  )
}
