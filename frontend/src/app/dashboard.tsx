'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { User } from '@supabase/supabase-js'
import { Button, Card, Badge, EmptyState, Progress } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'
import type { UserRole } from '@/components/shell/AppShell'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Organization {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  created_at: string
}

interface DashboardProps {
  user: User
  role: UserRole
  organizations: Organization[]
  credits: number
}

export default function Dashboard({ user, role, organizations, credits }: DashboardProps) {
  const router = useRouter()
  const firm = organizations[0]
  const hasFirm = !!firm
  const hasWsCode = !!firm?.ws_kodu

  const [stats, setStats] = useState({ activeSessions: 0, totalAnalyzed: 0 })
  const [recentSessions, setRecentSessions] = useState<Array<{ job_name: string; processed_products: number; created_at: string; status: string }>>([])

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${API}/api/stats`)
        if (res.ok) {
          const data = await res.json()
          setStats({ activeSessions: data.active_sessions || 0, totalAnalyzed: data.total_analyzed || 0 })
        }
      } catch { /* backend down */ }
    }
    fetchStats()
    const t = setInterval(fetchStats, 15000)
    return () => clearInterval(t)
  }, [])

  const firstName = user.email?.split('@')[0] || 'kullanıcı'

  return (
    <>
      {/* ── Hero Greeting ── */}
      <div className="hero">
        <div className="hero-text">
          <span className="hero-eyebrow">{role === 'admin' ? 'Admin Panel' : 'Dashboard'}</span>
          <h1>
            Merhaba, <span className="text-gradient">{firstName}</span>
          </h1>
          <p>
            {!hasFirm && 'Başlamak için firmanı ekle.'}
            {hasFirm && !hasWsCode && 'Ticimax entegrasyonunu tamamla ve ilk analizini başlat.'}
            {hasFirm && hasWsCode && `${firm.company_name} için AI içerik üretimine hazırsın.`}
          </p>
        </div>

        {hasFirm && hasWsCode && (
          <Button
            variant="gradient"
            size="lg"
            onClick={() => router.push('/seo')}
            icon={<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>}
          >
            Yeni Analiz Başlat
          </Button>
        )}
      </div>

      {/* ── Onboarding State ── */}
      {!hasFirm && (
        <Card variant="magic" padding="lg" className="onboarding-card">
          <div className="onb">
            <div className="onb-steps">
              <div className="step done">
                <div className="step-circle">✓</div>
                <div className="step-label">Hesap Oluşturuldu</div>
              </div>
              <div className="step-line" />
              <div className="step active">
                <div className="step-circle">2</div>
                <div className="step-label">Firma Ekle</div>
              </div>
              <div className="step-line" />
              <div className="step">
                <div className="step-circle">3</div>
                <div className="step-label">İlk Analiz</div>
              </div>
            </div>
            <h2>Pixra'ya hoş geldin! 🎉</h2>
            <p className="onb-desc">
              Başlamak için e-ticaret mağazanın bilgilerini ekle. <strong>İlk 10 ürün analizi bizden hediye.</strong>
            </p>
            <Button variant="gradient" size="lg" onClick={() => router.push('/onboarding')}>
              Kuruluma Başla →
            </Button>
          </div>
        </Card>
      )}

      {/* ── Stats Row ── */}
      {hasFirm && (
        <div className="stats-grid">
          <Card padding="md">
            <div className="stat">
              <div className="stat-head">
                <span className="stat-label">Analiz Kredin</span>
                <Badge tone={credits < 50 ? 'warning' : 'brand'} soft>{credits < 50 ? 'Düşük' : 'Aktif'}</Badge>
              </div>
              <div className="stat-value-row">
                <span className="stat-value">{credits.toLocaleString('tr-TR')}</span>
                <span className="stat-unit">ürün</span>
              </div>
              <Progress value={credits} max={Math.max(credits, 1000)} tone={credits < 50 ? 'warning' : 'brand'} size="sm" />
              <Link href="/credits" className="stat-link">Paket al →</Link>
            </div>
          </Card>

          <Card padding="md">
            <div className="stat">
              <div className="stat-head">
                <span className="stat-label">Toplam Analiz</span>
                <Badge tone="success" soft dot>Canlı</Badge>
              </div>
              <div className="stat-value-row">
                <span className="stat-value">{stats.totalAnalyzed.toLocaleString('tr-TR')}</span>
                <span className="stat-unit">ürün</span>
              </div>
              <span className="stat-sub">Bugüne kadar analiz edilen</span>
            </div>
          </Card>

          <Card padding="md">
            <div className="stat">
              <div className="stat-head">
                <span className="stat-label">Aktif İşlem</span>
                {stats.activeSessions > 0 ? <Badge tone="info" soft dot>İşleniyor</Badge> : <Badge tone="neutral" soft>Boşta</Badge>}
              </div>
              <div className="stat-value-row">
                <span className="stat-value">{stats.activeSessions}</span>
                <span className="stat-unit">oturum</span>
              </div>
              <span className="stat-sub">Şu an çalışan analiz sayısı</span>
            </div>
          </Card>
        </div>
      )}

      {/* ── Firm Status Card (customer has single firm) ── */}
      {hasFirm && role === 'customer' && (
        <section className="section">
          <PageHeader
            title="Mağazan"
            description="Entegrasyon durumu ve hızlı eylemler"
          />
          <Card padding="lg">
            <div className="firm-card">
              <div className="firm-header">
                <div className="firm-avatar">{firm.company_name[0]?.toUpperCase()}</div>
                <div className="firm-info">
                  <h3>{firm.company_name}</h3>
                  <span className="firm-domain">{firm.domain_url || 'Domain belirtilmemiş'}</span>
                </div>
                <div className="firm-badges">
                  <Badge tone={hasWsCode ? 'success' : 'warning'} dot>
                    Ticimax {hasWsCode ? 'Bağlı' : 'Eksik'}
                  </Badge>
                </div>
              </div>
              <div className="firm-actions">
                <Button variant="gradient" onClick={() => router.push('/seo')}>
                  Ürünleri Analiz Et
                </Button>
                <Button variant="ghost" onClick={() => router.push('/settings')}>
                  Ayarları Düzenle
                </Button>
              </div>
            </div>
          </Card>
        </section>
      )}

      {/* ── Agency/Admin: Firms Table ── */}
      {(role === 'agency' || role === 'admin') && organizations.length > 0 && (
        <section className="section">
          <PageHeader
            title={role === 'admin' ? 'Tüm Firmalar' : 'Müşteri Portföyüm'}
            description={`${organizations.length} aktif firma`}
            actions={
              <Button variant="primary" onClick={() => router.push('/onboarding')}>
                + Firma Ekle
              </Button>
            }
          />
          <div className="firm-list">
            {organizations.map(org => (
              <Card key={org.id} padding="md" interactive onClick={() => router.push(role === 'admin' ? '/admin' : '/seo')}>
                <div className="firm-row">
                  <div className="firm-avatar">{org.company_name[0]?.toUpperCase()}</div>
                  <div className="firm-row-info">
                    <span className="firm-row-name">{org.company_name}</span>
                    <span className="firm-row-domain">{org.domain_url || '—'}</span>
                  </div>
                  <Badge tone={org.ws_kodu ? 'success' : 'warning'} soft>
                    {org.ws_kodu ? '✓ Ticimax' : 'Kurulum Gerekli'}
                  </Badge>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* ── Recent Activity ── */}
      {hasFirm && (
        <section className="section">
          <PageHeader
            title="Son Analizler"
            description="Tamamlanan ve devam eden işlemler"
            actions={<Link href="/seo" className="section-link">Tümü →</Link>}
          />
          {recentSessions.length === 0 ? (
            <EmptyState
              icon={<svg width="28" height="28" viewBox="0 0 28 28" fill="none"><path d="M5 14H11V22H5V14ZM11 6H17V22H11V6ZM17 10H23V22H17V10Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /></svg>}
              title="Henüz analiz yapmadın"
              description="İlk analizinle beraber AI'ın ürünlerini nasıl optimize ettiğini göreceksin."
              action={
                hasWsCode && (
                  <Button variant="gradient" onClick={() => router.push('/seo')}>
                    İlk Analizi Başlat
                  </Button>
                )
              }
            />
          ) : (
            <div className="session-list">
              {/* render recentSessions here when data is available */}
            </div>
          )}
        </section>
      )}

      <style jsx>{`
        .hero {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 24px;
          margin-bottom: 32px;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border-subtle);
        }
        .hero-text { flex: 1; min-width: 0; }
        .hero-eyebrow {
          font-size: var(--text-xs);
          font-weight: var(--weight-semibold);
          color: var(--brand-text);
          text-transform: uppercase;
          letter-spacing: var(--tracking-caps);
          margin-bottom: 10px;
          display: block;
        }
        .hero h1 {
          font-size: var(--text-3xl);
          font-weight: var(--weight-bold);
          letter-spacing: var(--tracking-tight);
          margin: 0 0 8px;
        }
        .hero p {
          color: var(--text-tertiary);
          font-size: var(--text-md);
          margin: 0;
          max-width: 560px;
        }

        .onboarding-card {
          margin-bottom: 32px;
        }
        .onb {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          gap: 16px;
          padding: 24px 20px;
        }
        .onb-steps {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        .step {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          min-width: 90px;
        }
        .step-circle {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 2px solid var(--border-default);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: var(--weight-semibold);
          color: var(--text-tertiary);
          background: var(--surface-2);
        }
        .step.done .step-circle {
          background: var(--success);
          color: #fff;
          border-color: var(--success);
        }
        .step.active .step-circle {
          background: var(--brand-gradient);
          color: #fff;
          border-color: transparent;
          box-shadow: 0 0 0 4px var(--brand-subtle);
        }
        .step-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          font-weight: var(--weight-medium);
        }
        .step.done .step-label, .step.active .step-label {
          color: var(--text-primary);
        }
        .step-line {
          width: 40px;
          height: 2px;
          background: var(--border-default);
          border-radius: 1px;
        }
        .onb h2 {
          font-size: var(--text-xl);
          margin: 0;
        }
        .onb-desc {
          color: var(--text-secondary);
          max-width: 440px;
          line-height: 1.55;
        }
        .onb-desc strong {
          color: var(--brand-text);
          font-weight: var(--weight-semibold);
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          margin-bottom: 32px;
        }
        .stat {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .stat-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: var(--tracking-caps);
          font-weight: var(--weight-semibold);
        }
        .stat-value-row {
          display: flex;
          align-items: baseline;
          gap: 6px;
        }
        .stat-value {
          font-size: var(--text-2xl);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
          font-variant-numeric: tabular-nums;
          letter-spacing: var(--tracking-tight);
        }
        .stat-unit {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }
        .stat-sub {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .stat-link {
          color: var(--brand-text);
          font-size: var(--text-xs);
          font-weight: var(--weight-semibold);
          margin-top: auto;
        }
        .stat-link:hover { text-decoration: underline; }

        .section {
          margin-bottom: 40px;
        }
        .section-link {
          font-size: var(--text-sm);
          color: var(--brand-text);
          font-weight: var(--weight-semibold);
        }
        .section-link:hover { text-decoration: underline; }

        .firm-card {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .firm-header {
          display: flex;
          align-items: center;
          gap: 14px;
        }
        .firm-avatar {
          width: 48px;
          height: 48px;
          border-radius: var(--radius-lg);
          background: var(--brand-gradient);
          color: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: var(--weight-bold);
          font-size: var(--text-lg);
          flex-shrink: 0;
        }
        .firm-info {
          flex: 1;
          min-width: 0;
        }
        .firm-info h3 {
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          margin: 0 0 4px;
        }
        .firm-domain {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
        }
        .firm-badges {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }
        .firm-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .firm-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 12px;
        }
        .firm-row {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .firm-row .firm-avatar {
          width: 36px;
          height: 36px;
          font-size: var(--text-sm);
          border-radius: var(--radius-md);
        }
        .firm-row-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
        }
        .firm-row-name {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }
        .firm-row-domain {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        @media (max-width: 900px) {
          .hero { flex-direction: column; align-items: stretch; }
          .stats-grid { grid-template-columns: 1fr; }
          .onb-steps { flex-wrap: wrap; justify-content: center; }
          .step-line { display: none; }
        }
      `}</style>
    </>
  )
}
