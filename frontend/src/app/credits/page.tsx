import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import CreditsClient from './credits-client'

export default async function CreditsPage() {
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  const { user, role, db } = eff

  const { data: firm } = await db
    .from('organizations')
    .select('id, company_name')
    .eq('user_id', user.id)
    .maybeSingle()

  const { data: creditRow } = await db
    .from('credits')
    .select('balance')
    .eq('user_id', user.id)
    .maybeSingle()

  const credits = creditRow?.balance ?? 10

  const { data: sessions } = await db
    .from('ai_sessions')
    .select('id, job_name, total_products, processed_products, created_at')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(20)

  return (
    <AppShell user={user} role={role} credits={credits} firmName={firm?.company_name} impersonation={eff.impersonation}>
      <CreditsClient credits={credits} sessions={sessions || []} userId={user.id} />
    </AppShell>
  )
}
