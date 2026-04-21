import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import ComingSoon from '@/components/shell/ComingSoon'

export default async function AdsPage() {
  const eff = await getEffectiveUser()
  if (!eff) redirect('/login')
  const { user, role, db } = eff

  const { data: firm } = await db
    .from('organizations').select('company_name').eq('user_id', user.id).maybeSingle()

  const { data: creditRow } = await db
    .from('credits').select('balance').eq('user_id', user.id).maybeSingle()

  return (
    <AppShell user={user} role={role} credits={creditRow?.balance ?? 10} firmName={firm?.company_name} impersonation={eff.impersonation}>
      <ComingSoon
        module="ads"
        icon="📣"
        title="Reklam Yönetimi"
        pitch="Google Ads ve Meta reklamlarını AI ile optimize et. Kampanya kurulumu, bütçe önerileri, metin üretimi ve performans analizi — hepsi tek yerde."
        features={[
          'AI destekli reklam metni üretimi',
          'Otomatik anahtar kelime keşfi',
          'Bütçe önerileri ve ROAS tahmini',
          'Google Ads + Meta tek panelden yönetim',
          'Rakip analizi',
        ]}
        userId={user.id}
        email={user.email || ''}
      />
    </AppShell>
  )
}
