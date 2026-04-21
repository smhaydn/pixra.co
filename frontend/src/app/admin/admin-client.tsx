'use client'

import { useRouter } from 'next/navigation'
import { Card, Badge, Button, EmptyState } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'

interface Kpis {
  users: number
  firms: number
  sessions: number
}

interface SessionRow {
  id: string
  job_name: string
  status: string
  total_products: number
  processed_products: number
  created_at: string
  organizations: { company_name: string } | { company_name: string }[] | null
}

interface FirmRow {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  created_at: string
  user_id: string
}

function firmName(s: SessionRow): string {
  const o = s.organizations
  if (!o) return '—'
  if (Array.isArray(o)) return o[0]?.company_name || '—'
  return o.company_name || '—'
}

export default function AdminClient({ kpis, recentSessions, firms }: { kpis: Kpis; recentSessions: SessionRow[]; firms: FirmRow[] }) {
  const router = useRouter()

  return (
    <>
      <PageHeader
        title="Admin Paneli"
        description="Pixra sistem geneli — müşteriler, analizler, sağlık"
        actions={<Badge tone="brand" soft>Internal</Badge>}
      />

      <div className="kpi-grid">
        <Card variant="elevated" padding="md">
          <div className="kpi">
            <span className="label">Toplam Müşteri</span>
            <div className="val">{kpis.users.toLocaleString('tr-TR')}</div>
            <span className="sub">Kayıtlı firma sahibi</span>
          </div>
        </Card>
        <Card variant="elevated" padding="md">
          <div className="kpi">
            <span className="label">Toplam Firma</span>
            <div className="val">{kpis.firms.toLocaleString('tr-TR')}</div>
            <span className="sub">Onboarding tamamlanan</span>
          </div>
        </Card>
        <Card variant="elevated" padding="md">
          <div className="kpi">
            <span className="label">Toplam Analiz Oturumu</span>
            <div className="val">{kpis.sessions.toLocaleString('tr-TR')}</div>
            <span className="sub">Tüm zamanlar</span>
          </div>
        </Card>
      </div>

      <section className="admin-section">
        <div className="sec-head">
          <h2>Son Analizler</h2>
          <span className="muted">{recentSessions.length} kayıt gösteriliyor</span>
        </div>
        {recentSessions.length === 0 ? (
          <EmptyState title="Henüz analiz yok" description="Müşteriler oturum başlattıkça burada görünecek." />
        ) : (
          <Card padding="none">
            <table className="tbl">
              <thead>
                <tr>
                  <th>İş</th>
                  <th>Firma</th>
                  <th>Durum</th>
                  <th>İlerleme</th>
                  <th>Tarih</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recentSessions.map(s => {
                  const status = s.status as 'pending' | 'processing' | 'completed' | 'failed'
                  return (
                    <tr key={s.id}>
                      <td className="primary">{s.job_name}</td>
                      <td>{firmName(s)}</td>
                      <td>
                        <Badge
                          tone={status === 'completed' ? 'success' : status === 'processing' ? 'info' : status === 'failed' ? 'danger' : 'neutral'}
                          dot
                        >
                          {status === 'completed' && 'Tamamlandı'}
                          {status === 'processing' && 'İşleniyor'}
                          {status === 'pending' && 'Bekliyor'}
                          {status === 'failed' && 'Hata'}
                        </Badge>
                      </td>
                      <td>{s.processed_products}/{s.total_products}</td>
                      <td>{new Date(s.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                      <td>
                        <Button variant="ghost" size="sm" onClick={() => router.push(`/seo/session/${s.id}`)}>
                          Gör →
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Card>
        )}
      </section>

      <section className="admin-section">
        <div className="sec-head">
          <h2>Müşteriler</h2>
          <span className="muted">{firms.length} firma</span>
        </div>
        {firms.length === 0 ? (
          <EmptyState title="Firma yok" description="Henüz hiçbir müşteri onboarding'i tamamlamadı." />
        ) : (
          <Card padding="none">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Firma</th>
                  <th>Domain</th>
                  <th>Ticimax</th>
                  <th>Kayıt</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {firms.map(f => (
                  <tr key={f.id}>
                    <td className="primary">{f.company_name}</td>
                    <td className="muted">{f.domain_url || '—'}</td>
                    <td>
                      {f.ws_kodu ? (
                        <Badge tone="success" soft>Bağlı</Badge>
                      ) : (
                        <Badge tone="warning" soft>Eksik</Badge>
                      )}
                    </td>
                    <td>{new Date(f.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                    <td>
                      <Button variant="ghost" size="sm" onClick={() => router.push(`/admin/customers/${f.user_id}`)}>
                        Detay →
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </section>

      <style jsx>{`
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          margin-bottom: 32px;
        }
        .kpi {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .kpi .label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: var(--weight-medium);
        }
        .kpi .val {
          font-size: var(--text-3xl);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
          line-height: 1.1;
        }
        .kpi .sub {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .admin-section {
          margin-bottom: 32px;
        }
        .sec-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .sec-head h2 {
          font-size: var(--text-xl);
          font-weight: var(--weight-semibold);
          margin: 0;
        }
        .muted {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .tbl {
          width: 100%;
          border-collapse: collapse;
        }
        .tbl th {
          text-align: left;
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-subtle);
        }
        .tbl td {
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-subtle);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .tbl tr:last-child td { border-bottom: none; }
        .tbl td.primary {
          color: var(--text-primary);
          font-weight: var(--weight-medium);
        }

        @media (max-width: 800px) {
          .kpi-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </>
  )
}
