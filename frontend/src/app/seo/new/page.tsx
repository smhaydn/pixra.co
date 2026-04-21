import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import NewAnalysisClient from './new-client'

export default async function NewAnalysisPage() {
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  const { user, role, db } = eff

  const { data: firm } = await db
    .from('organizations')
    .select('*')
    .eq('user_id', user.id)
    .maybeSingle()

  if (!firm || !firm.ws_kodu || !firm.domain_url) redirect('/seo')

  const { data: creditRow } = await db
    .from('credits')
    .select('balance')
    .eq('user_id', user.id)
    .maybeSingle()

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 0} firmName={firm.company_name} impersonation={eff.impersonation}>
      <NewAnalysisClient
        firm={{
          id: firm.id,
          company_name: firm.company_name,
          domain_url: firm.domain_url,
          ws_kodu: firm.ws_kodu,
          gemini_api_key: firm.gemini_api_key,
        }}
        userId={user.id}
        credits={creditRow?.balance ?? 0}
        readOnly={!!eff.impersonation}
      />
    </AppShell>
  )
}
