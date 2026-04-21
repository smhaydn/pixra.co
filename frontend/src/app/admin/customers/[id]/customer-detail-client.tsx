'use client'

import { useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'
import { Button, Card, Badge, Input, EmptyState, useToast } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'
import { startImpersonate, adjustCredits } from '../actions'

interface Target {
  id: string
  email: string | null
  created_at: string
  last_sign_in_at: string | null
  full_name: string | null
  role: string
}

interface Firm {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  created_at: string
}

interface Session {
  id: string
  job_name: string
  status: string
  total_products: number
  processed_products: number
  created_at: string
}

interface Adjustment {
  id: string
  delta: number
  balance_after: number
  note: string | null
  created_at: string
}

interface Props {
  target: Target
  firm: Firm | null
  credits: number
  creditsUpdatedAt: string | null
  sessions: Session[]
  adjustments: Adjustment[]
}

export default function CustomerDetailClient({ target, firm, credits, creditsUpdatedAt, sessions, adjustments }: Props) {
  const toast = useToast()
  const router = useRouter()
  const [pending, start] = useTransition()

  const [delta, setDelta] = useState('100')
  const [note, setNote] = useState('')
  const [adjusting, setAdjusting] = useState(false)

  const impersonate = () => {
    if (!confirm(`${target.email || target.id} olarak görüntülemeye başlanacak. Tüm aksiyonlar salt-okunur. Devam?`)) return
    start(() => startImpersonate(target.id))
  }

  const submitAdjust = async () => {
    const d = parseInt(delta, 10)
    if (!Number.isFinite(d) || d === 0) return toast.show('Geçerli bir miktar gir (+ veya -)', 'warning')
    if (!note.trim()) return toast.show('Sebep yaz', 'warning')
    setAdjusting(true)
    try {
      await adjustCredits(target.id, d, note.trim())
      toast.show(`Kredi güncellendi: ${d > 0 ? '+' : ''}${d}`, 'success')
      setNote('')
      setDelta('100')
      router.refresh()
    } catch (e) {
      toast.show(e instanceof Error ? e.message : 'Hata', 'error')
    } finally {
      setAdjusting(false)
    }
  }

  const totalUsed = sessions.reduce((sum, s) => sum + s.processed_products, 0)

  return (
    <>
      <PageHeader
        title={target.full_name || target.email || target.id}
        description={target.email || undefined}
        actions={
          <>
            <Badge tone={target.role === 'admin' ? 'brand' : target.role === 'agency' ? 'info' : 'neutral'} soft>
              {target.role}
            </Badge>
            <Button variant="gradient" onClick={impersonate} loading={pending}>
              🎭 Impersonate
            </Button>
          </>
        }
      />

      <div className="cust-grid">
        <Card padding="md" variant="elevated">
          <div className="kpi">
            <span className="label">Bakiye</span>
            <div className="val">{credits.toLocaleString('tr-TR')}</div>
            <span className="sub">
              {creditsUpdatedAt
                ? `Son güncelleme: ${new Date(creditsUpdatedAt).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}`
                : 'Henüz kredi yok'}
            </span>
          </div>
        </Card>
        <Card padding="md" variant="elevated">
          <div className="kpi">
            <span className="label">Toplam Analiz</span>
            <div className="val">{totalUsed.toLocaleString('tr-TR')}</div>
            <span className="sub">{sessions.length} oturum</span>
          </div>
        </Card>
        <Card padding="md" variant="elevated">
          <div className="kpi">
            <span className="label">Kayıt</span>
            <div className="val small">
              {new Date(target.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}
            </div>
            <span className="sub">
              Son giriş: {target.last_sign_in_at
                ? new Date(target.last_sign_in_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })
                : '—'}
            </span>
          </div>
        </Card>
      </div>

      <div className="cust-split">
        <section>
          <h2>Firma</h2>
          {firm ? (
            <Card padding="md">
              <div className="firm-info">
                <div>
                  <span className="f-label">İsim</span>
                  <strong>{firm.company_name}</strong>
                </div>
                <div>
                  <span className="f-label">Domain</span>
                  <strong>{firm.domain_url || '—'}</strong>
                </div>
                <div>
                  <span className="f-label">Ticimax WS</span>
                  {firm.ws_kodu ? (
                    <Badge tone="success" soft>Bağlı · {firm.ws_kodu.slice(0, 8)}…</Badge>
                  ) : (
                    <Badge tone="warning" soft>Eksik</Badge>
                  )}
                </div>
              </div>
            </Card>
          ) : (
            <Card padding="md" variant="flat">
              <p className="muted">Onboarding tamamlanmamış</p>
            </Card>
          )}

          <h2 style={{ marginTop: 24 }}>Kredi Ayarlama</h2>
          <Card padding="md">
            <div className="adjust">
              <div className="adjust-row">
                <Input
                  label="Miktar (+/-)"
                  type="number"
                  value={delta}
                  onChange={e => setDelta(e.target.value)}
                  hint="Pozitif: ekle, Negatif: düş"
                />
                <Input
                  label="Sebep"
                  value={note}
                  onChange={e => setNote(e.target.value)}
                  placeholder="Örn: İade, destek hediyesi, beta teşvik"
                />
              </div>
              <div className="adjust-quick">
                <span className="muted">Hızlı:</span>
                {[100, 500, 1000, -50].map(v => (
                  <button key={v} className="quick-chip" onClick={() => setDelta(String(v))}>
                    {v > 0 ? `+${v}` : v}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button variant="gradient" onClick={submitAdjust} loading={adjusting}>
                  Uygula
                </Button>
              </div>
            </div>
          </Card>

          {adjustments.length > 0 && (
            <>
              <h3 className="sub-heading">Son Ayarlamalar</h3>
              <Card padding="none">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Değişim</th>
                      <th>Bakiye Sonrası</th>
                      <th>Not</th>
                      <th>Tarih</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adjustments.map(a => (
                      <tr key={a.id}>
                        <td className={a.delta > 0 ? 'pos' : 'neg'}>
                          {a.delta > 0 ? `+${a.delta}` : a.delta}
                        </td>
                        <td>{a.balance_after}</td>
                        <td className="muted">{a.note || '—'}</td>
                        <td>{new Date(a.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            </>
          )}
        </section>

        <section>
          <h2>Analiz Oturumları</h2>
          {sessions.length === 0 ? (
            <EmptyState title="Henüz analiz yok" description="Müşteri ilk oturumunu başlatmadı." />
          ) : (
            <Card padding="none">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>İş</th>
                    <th>Durum</th>
                    <th>İlerleme</th>
                    <th>Tarih</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map(s => {
                    const status = s.status as 'pending' | 'processing' | 'completed' | 'failed'
                    return (
                      <tr key={s.id} className="clickable" onClick={() => router.push(`/seo/session/${s.id}`)}>
                        <td className="primary">{s.job_name}</td>
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
                        <td>{new Date(s.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </Card>
          )}
        </section>
      </div>

      <style jsx>{`
        .cust-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          margin-bottom: 28px;
        }
        .kpi {
          display: flex;
          flex-direction: column;
          gap: 4px;
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
        .kpi .val.small { font-size: var(--text-lg); }
        .kpi .sub {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .cust-split {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          align-items: start;
        }
        h2 {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          margin: 0 0 12px;
        }
        .sub-heading {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          margin: 20px 0 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: var(--weight-medium);
        }
        .muted { color: var(--text-tertiary); font-size: var(--text-sm); margin: 0; }

        .firm-info {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .firm-info div {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          font-size: var(--text-sm);
        }
        .f-label { color: var(--text-tertiary); }
        .firm-info strong { color: var(--text-primary); font-weight: var(--weight-medium); }

        .adjust {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .adjust-row {
          display: grid;
          grid-template-columns: 140px 1fr;
          gap: 12px;
        }
        .adjust-quick {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: var(--text-xs);
        }
        .quick-chip {
          padding: 4px 10px;
          border-radius: 999px;
          background: var(--surface-2);
          border: 1px solid var(--border-subtle);
          color: var(--text-secondary);
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
        }
        .quick-chip:hover {
          background: var(--brand-subtle);
          border-color: var(--brand-border);
          color: var(--brand-text);
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
          padding: 12px 14px;
          border-bottom: 1px solid var(--border-subtle);
        }
        .tbl td {
          padding: 12px 14px;
          border-bottom: 1px solid var(--border-subtle);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .tbl tr:last-child td { border-bottom: none; }
        .tbl td.primary { color: var(--text-primary); font-weight: var(--weight-medium); }
        .tbl td.pos { color: var(--success-text); font-weight: var(--weight-semibold); }
        .tbl td.neg { color: var(--error-text); font-weight: var(--weight-semibold); }
        .tbl tr.clickable { cursor: pointer; transition: background var(--duration-fast) var(--ease-out); }
        .tbl tr.clickable:hover { background: var(--surface-2); }

        @media (max-width: 1000px) {
          .cust-split { grid-template-columns: 1fr; }
        }
        @media (max-width: 700px) {
          .cust-grid { grid-template-columns: 1fr; }
          .adjust-row { grid-template-columns: 1fr; }
        }
      `}</style>
    </>
  )
}
