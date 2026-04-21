import { redirect, notFound } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import SessionClient from './session-client'

export default async function SessionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  const { user, role, db } = eff

  const { data: session } = await db
    .from('ai_sessions')
    .select('*, organizations(id, company_name, ws_kodu, domain_url)')
    .eq('id', id)
    .maybeSingle()

  if (!session) notFound()

  const { data: results } = await db
    .from('ai_results')
    .select('*')
    .eq('session_id', id)
    .order('created_at', { ascending: true })

  const { data: creditRow } = await db
    .from('credits')
    .select('balance')
    .eq('user_id', user.id)
    .maybeSingle()

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 10} firmName={session.organizations?.company_name} impersonation={eff.impersonation}>
      <SessionClient session={session} initialResults={results || []} />
    </AppShell>
  )
}
