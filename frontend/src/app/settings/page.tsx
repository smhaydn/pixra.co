import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import SettingsClient from './settings-client'

export default async function SettingsPage() {
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  const { user, role, db } = eff

  const { data: firm } = await db
    .from('organizations')
    .select('*')
    .eq('user_id', user.id)
    .maybeSingle()

  const { data: creditRow } = await db
    .from('credits')
    .select('balance')
    .eq('user_id', user.id)
    .maybeSingle()

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 10} firmName={firm?.company_name} impersonation={eff.impersonation}>
      <SettingsClient user={user} firm={firm} readOnly={!!eff.impersonation} />
    </AppShell>
  )
}
