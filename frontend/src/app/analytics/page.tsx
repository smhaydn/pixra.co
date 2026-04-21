import { redirect } from 'next/navigation'
import { AppShell } from '@/components/shell/AppShell'
import { getEffectiveUser } from '@/lib/auth/effective-user'
import ComingSoon from '@/components/shell/ComingSoon'

export default async function AnalyticsPage() {
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
        module="analytics"
        icon="📊"
        title="Analitik & Raporlama"
        pitch="Satış, trafik ve SEO performansını tek dashboard'da gör. Hangi ürün kazanıyor, hangi sayfa sızdırıyor — AI sana söylesin."
        features={[
          'Gerçek zamanlı satış ve trafik dashboardu',
          'Ürün bazında SEO performans skoru',
          'Anomali tespiti (satış düşüşü, trafik kaybı)',
          'Google Search Console + Analytics entegrasyonu',
          'Haftalık AI içgörü raporu',
        ]}
        userId={user.id}
        email={user.email || ''}
      />
    </AppShell>
  )
}
