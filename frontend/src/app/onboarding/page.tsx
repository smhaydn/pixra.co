import { redirect } from 'next/navigation'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import OnboardingClient from './onboarding-client'

export default async function OnboardingPage() {
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  // Impersonate modunda onboarding yapılamaz
  if (eff.impersonation) redirect('/admin')

  const { data: existing } = await eff.db
    .from('organizations')
    .select('*')
    .eq('user_id', eff.user.id)
    .maybeSingle()

  return <OnboardingClient userId={eff.user.id} existing={existing} />
}
