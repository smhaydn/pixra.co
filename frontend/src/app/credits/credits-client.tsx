'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Badge, Input, Modal, useToast } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'

interface Session {
  id: string
  job_name: string
  total_products: number
  processed_products: number
  created_at: string
}

interface Package {
  id: string
  name: string
  credits: number
  price: number
  perUnit: number
  tag?: string
  highlight?: boolean
  features: string[]
}

const PACKAGES: Package[] = [
  {
    id: 'starter',
    name: 'Başlangıç',
    credits: 500,
    price: 490,
    perUnit: 0.98,
    features: ['500 ürün analizi', 'E-posta destek', 'Ticimax entegrasyonu'],
  },
  {
    id: 'pro',
    name: 'Pro',
    credits: 1500,
    price: 1290,
    perUnit: 0.86,
    tag: 'En Popüler',
    highlight: true,
    features: ['1.500 ürün analizi', 'Öncelikli destek', 'Toplu Ticimax güncelleme', 'Kampanya önerileri'],
  },
  {
    id: 'agency',
    name: 'Ajans',
    credits: 5000,
    price: 3990,
    perUnit: 0.80,
    features: ['5.000 ürün analizi', 'Çoklu firma yönetimi', 'WhatsApp destek hattı', 'API erişimi'],
  },
]

export default function CreditsClient({ credits, sessions, userId }: { credits: number; sessions: Session[]; userId: string }) {
  const toast = useToast()
  const supabase = createClient()

  const [waitOpen, setWaitOpen] = useState<Package | null>(null)
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const totalUsed = sessions.reduce((sum, s) => sum + s.processed_products, 0)
  const thisMonth = sessions
    .filter(s => new Date(s.created_at).getMonth() === new Date().getMonth())
    .reduce((sum, s) => sum + s.processed_products, 0)

  const handleInterest = async () => {
    if (!waitOpen) return
    if (!email.trim() || !email.includes('@')) return toast.show('Geçerli bir e-posta gir', 'warning')
    setSubmitting(true)
    await supabase.from('waitlist').insert({
      user_id: userId,
      email,
      package_id: waitOpen.id,
      package_name: waitOpen.name,
    })
    setSubmitting(false)
    setWaitOpen(null)
    setEmail('')
    toast.show('Kaydedildi — sana özel teklifle döneceğiz 🎁', 'success')
  }

  return (
    <>
      <PageHeader
        title="Krediler"
        description="Analiz paketleri ve kullanım geçmişin"
      />

      <div className="balance-wrap">
        <Card variant="magic" padding="lg">
          <div className="balance">
            <div>
              <span className="balance-label">Mevcut Bakiye</span>
              <div className="balance-value">
                <span className="num">{credits.toLocaleString('tr-TR')}</span>
                <span className="unit">analiz</span>
              </div>
              {credits <= 10 && (
                <Badge tone="warning" soft style={{ marginTop: 8 }}>
                  Düşük bakiye — yakında bitecek
                </Badge>
              )}
            </div>
            <div className="balance-stats">
              <div className="bstat">
                <span>Bu ay kullanılan</span>
                <strong>{thisMonth.toLocaleString('tr-TR')}</strong>
              </div>
              <div className="bstat">
                <span>Toplam kullanılan</span>
                <strong>{totalUsed.toLocaleString('tr-TR')}</strong>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <section className="packages-section">
        <div className="sec-head">
          <h2>Paketler</h2>
          <span className="beta-note">
            <Badge tone="info" soft>Beta</Badge>
            Ödeme entegrasyonu yakında — şimdilik e-posta ile rezervasyon
          </span>
        </div>

        <div className="packages">
          {PACKAGES.map(pkg => (
            <div key={pkg.id} className={`pkg-wrap ${pkg.highlight ? 'highlight' : ''}`}>
              {pkg.tag && <div className="pkg-tag">{pkg.tag}</div>}
              <Card variant={pkg.highlight ? 'magic' : 'elevated'} padding="lg">
                <div className="pkg">
                  <h3>{pkg.name}</h3>
                  <div className="price">
                    <span className="price-num">₺{pkg.price.toLocaleString('tr-TR')}</span>
                    <span className="price-unit">/ tek seferlik</span>
                  </div>
                  <div className="per-unit">
                    <strong>{pkg.credits.toLocaleString('tr-TR')}</strong> analiz ·
                    <span className="unit-price"> ₺{pkg.perUnit.toFixed(2)}/ürün</span>
                  </div>
                  <ul className="features">
                    {pkg.features.map(f => (
                      <li key={f}>
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <path d="M3 7L6 10L11 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    variant={pkg.highlight ? 'gradient' : 'secondary'}
                    size="md"
                    onClick={() => setWaitOpen(pkg)}
                    style={{ width: '100%' }}
                  >
                    İlgileniyorum
                  </Button>
                </div>
              </Card>
            </div>
          ))}
        </div>
      </section>

      <section className="history-section">
        <h2>Kullanım Geçmişi</h2>
        {sessions.length === 0 ? (
          <Card padding="lg" variant="flat">
            <p className="empty-note">Henüz analiz yapılmadı. İlk analizini başlatmak için SEO sayfasına git.</p>
          </Card>
        ) : (
          <Card padding="none" variant="default">
            <table className="history-table">
              <thead>
                <tr>
                  <th>İş Adı</th>
                  <th>Ürün</th>
                  <th>İşlenen</th>
                  <th>Tarih</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => (
                  <tr key={s.id}>
                    <td className="job-name">{s.job_name}</td>
                    <td>{s.total_products}</td>
                    <td>{s.processed_products}</td>
                    <td>{new Date(s.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </section>

      <Modal
        open={!!waitOpen}
        onClose={() => setWaitOpen(null)}
        title={waitOpen ? `${waitOpen.name} paketi — ${waitOpen.credits.toLocaleString('tr-TR')} analiz` : ''}
        description="Ödeme sistemimiz çok yakında aktif olacak. E-postanı bırak, ilk sıraya al."
        footer={
          <>
            <Button variant="ghost" onClick={() => setWaitOpen(null)}>İptal</Button>
            <Button variant="gradient" onClick={handleInterest} loading={submitting}>
              Rezerve Et
            </Button>
          </>
        }
      >
        <Input
          type="email"
          label="E-posta"
          placeholder="ornek@firman.com"
          value={email}
          onChange={e => setEmail(e.target.value)}
          hint="Seni ödeme açıldığında bilgilendireceğiz — erken kayıt indirimi garantili."
        />
      </Modal>

      <style jsx>{`
        .balance-wrap {
          margin-bottom: 24px;
        }
        .balance {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 24px;
          flex-wrap: wrap;
        }
        .balance-label {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: var(--weight-medium);
        }
        .balance-value {
          display: flex;
          align-items: baseline;
          gap: 10px;
          margin-top: 4px;
        }
        .balance-value .num {
          font-size: var(--text-display);
          font-weight: var(--weight-bold);
          background: var(--brand-gradient);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          line-height: 1;
        }
        .balance-value .unit {
          font-size: var(--text-base);
          color: var(--text-tertiary);
        }
        .balance-stats {
          display: flex;
          gap: 32px;
        }
        .bstat {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .bstat span {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .bstat strong {
          font-size: var(--text-xl);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .packages-section {
          margin-bottom: 32px;
        }
        .sec-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 16px;
          flex-wrap: wrap;
        }
        .sec-head h2 {
          font-size: var(--text-xl);
          font-weight: var(--weight-semibold);
          margin: 0;
        }
        .beta-note {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .packages {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
        }
        .pkg-wrap {
          position: relative;
        }
        .pkg-wrap.highlight {
          transform: translateY(-8px);
        }
        .pkg-tag {
          position: absolute;
          top: -10px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 2;
          background: var(--brand-gradient);
          color: #fff;
          padding: 4px 12px;
          border-radius: 999px;
          font-size: var(--text-xs);
          font-weight: var(--weight-semibold);
          box-shadow: var(--shadow-md);
        }
        .pkg {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .pkg h3 {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          margin: 0;
        }
        .price {
          display: flex;
          align-items: baseline;
          gap: 6px;
        }
        .price-num {
          font-size: var(--text-3xl);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }
        .price-unit {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .per-unit {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          padding-bottom: 12px;
          border-bottom: 1px solid var(--border-subtle);
        }
        .per-unit strong { color: var(--text-primary); }
        .unit-price { color: var(--text-tertiary); }
        .features {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
          min-height: 120px;
        }
        .features li {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .features svg {
          color: var(--success-text);
          flex-shrink: 0;
        }

        .history-section h2 {
          font-size: var(--text-xl);
          font-weight: var(--weight-semibold);
          margin: 0 0 16px;
        }
        .empty-note {
          color: var(--text-tertiary);
          text-align: center;
          margin: 0;
          font-size: var(--text-sm);
        }
        .history-table {
          width: 100%;
          border-collapse: collapse;
        }
        .history-table th {
          text-align: left;
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-subtle);
        }
        .history-table td {
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-subtle);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .history-table tr:last-child td { border-bottom: none; }
        .job-name { color: var(--text-primary); font-weight: var(--weight-medium); }

        @media (max-width: 900px) {
          .packages { grid-template-columns: 1fr; }
          .pkg-wrap.highlight { transform: none; }
        }
      `}</style>
    </>
  )
}
