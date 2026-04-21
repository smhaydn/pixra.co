import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import SeoClient from './seo-client'

export default async function SeoPage() {
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  const { user, role, db } = eff

  const { data: organizations } = await db
    .from('organizations')
    .select('*')
    .eq('user_id', user.id)

  const firm = organizations?.[0]

  const { data: creditRow } = await db
    .from('credits')
    .select('balance')
    .eq('user_id', user.id)
    .maybeSingle()

  const { data: sessions } = firm
    ? await db
        .from('ai_sessions')
        .select('*')
        .eq('organization_id', firm.id)
        .order('created_at', { ascending: false })
        .limit(20)
    : { data: [] }

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 10} firmName={firm?.company_name} impersonation={eff.impersonation}>
      <SeoClient firm={firm || null} sessions={sessions || []} userId={user.id} credits={creditRow?.balance ?? 10} />
    </AppShell>
  )
}
