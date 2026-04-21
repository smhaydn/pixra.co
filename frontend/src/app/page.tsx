import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import Dashboard from './dashboard'

export default async function HomePage() {
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

  const credits = creditRow?.balance ?? 10

  return (
    <AppShell user={user} role={role} credits={credits} firmName={firm?.company_name} impersonation={eff.impersonation}>
      <Dashboard user={user} role={role} organizations={organizations || []} credits={credits} />
    </AppShell>
  )
}
