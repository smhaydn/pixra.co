'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'
import { Button, Card, Input, Badge, useToast } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'

interface Firm {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  firma_profil?: Record<string, unknown> | null
  llms_txt_generated_at?: string | null
}

type Tab = 'profile' | 'firm' | 'billing'

export default function SettingsClient({ user, firm, readOnly = false }: { user: User; firm: Firm | null; readOnly?: boolean }) {
  const [tab, setTab] = useState<Tab>('profile')
  const [saving, setSaving] = useState(false)
  const [logouting, setLogouting] = useState(false)
  const toast = useToast()
  const router = useRouter()
  const supabase = createClient()

  const [profile, setProfile] = useState({
    full_name: user.user_metadata?.full_name || '',
    email: user.email || '',
  })
  const [firmForm, setFirmForm] = useState({
    company_name: firm?.company_name || '',
    domain_url: firm?.domain_url || '',
    ws_kodu: firm?.ws_kodu || '',
  })

  const saveProfile = async () => {
    if (readOnly) return toast.show('Impersonate modunda değiştirilemez', 'warning')
    setSaving(true)
    await supabase.auth.updateUser({ data: { full_name: profile.full_name } })
    setSaving(false)
    toast.show('Profil güncellendi', 'success')
    router.refresh()
  }

  const saveFirm = async () => {
    if (!firm) return
    if (readOnly) return toast.show('Impersonate modunda değiştirilemez', 'warning')
    setSaving(true)
    await supabase.from('organizations').update({
      company_name: firmForm.company_name,
      domain_url: firmForm.domain_url || null,
      ws_kodu: firmForm.ws_kodu || null,
    }).eq('id', firm.id)
    setSaving(false)
    toast.show('Firma bilgileri güncellendi', 'success')
    router.refresh()
  }

  const [llmsLoading, setLlmsLoading] = useState(false)

  const logout = async () => {
    setLogouting(true)
    await supabase.auth.signOut()
    router.push('/login')
  }

  const downloadLlmsTxt = async () => {
    if (!firm) return
    setLlmsLoading(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/llms-txt/${firm.id}`)
      if (!res.ok) throw new Error('Üretim hatası')
      const text = await res.text()
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'llms.txt'
      a.click()
      URL.revokeObjectURL(url)
      toast.show('llms.txt indirildi. Ticimax root klasörüne yükleyin.', 'success')
      router.refresh()
    } catch {
      toast.show('llms.txt üretilemedi', 'error')
    } finally {
      setLlmsLoading(false)
    }
  }

  return (
    <>
      <PageHeader title="Ayarlar" description="Hesabını ve firma bilgilerini yönet" />

      <div className="settings-layout">
        <nav className="tabs">
          <button className={`tab ${tab === 'profile' ? 'active' : ''}`} onClick={() => setTab('profile')}>
            <span className="tab-ico">👤</span>
            <div>
              <strong>Profil</strong>
              <small>Kişisel bilgilerin</small>
            </div>
          </button>
          <button className={`tab ${tab === 'firm' ? 'active' : ''}`} onClick={() => setTab('firm')}>
            <span className="tab-ico">🏢</span>
            <div>
              <strong>Firma</strong>
              <small>Ticimax bağlantısı</small>
            </div>
          </button>
          <button className={`tab ${tab === 'billing' ? 'active' : ''}`} onClick={() => setTab('billing')}>
            <span className="tab-ico">💳</span>
            <div>
              <strong>Fatura</strong>
              <small>Ödeme bilgileri</small>
            </div>
          </button>
        </nav>

        <div className="tab-body">
          {tab === 'profile' && (
            <Card padding="lg">
              <h2>Profil</h2>
              <p className="desc">Bu bilgiler hesabında görünür, dış taraflarla paylaşılmaz.</p>
              <div className="fields">
                <Input
                  label="Ad Soyad"
                  value={profile.full_name}
                  onChange={e => setProfile({ ...profile, full_name: e.target.value })}
                />
                <Input
                  label="E-posta"
                  value={profile.email}
                  disabled
                  hint="E-posta değişikliği için destek ile iletişime geç."
                />
              </div>
              <div className="actions">
                <Button variant="danger" onClick={logout} loading={logouting}>Çıkış Yap</Button>
                <Button variant="gradient" onClick={saveProfile} loading={saving}>Kaydet</Button>
              </div>
            </Card>
          )}

          {tab === 'firm' && (
            <>
              {!firm ? (
                <Card padding="lg" variant="flat">
                  <h2>Firma kurulmamış</h2>
                  <p className="desc">Önce onboarding'i tamamlaman gerek.</p>
                  <Button variant="gradient" onClick={() => router.push('/onboarding')}>Firma Kur</Button>
                </Card>
              ) : (
                <Card padding="lg">
                  <div className="sec-head">
                    <h2>Firma Bilgileri</h2>
                    {firmForm.ws_kodu ? (
                      <Badge tone="success" dot>Ticimax bağlı</Badge>
                    ) : (
                      <Badge tone="warning" dot>Ticimax bağlantısı eksik</Badge>
                    )}
                  </div>
                  <p className="desc">Ticimax WS kodun burada saklanır; analizler bu kodla senkronize olur.</p>
                  <div className="fields">
                    <Input
                      label="Firma Adı"
                      value={firmForm.company_name}
                      onChange={e => setFirmForm({ ...firmForm, company_name: e.target.value })}
                    />
                    <Input
                      label="Mağaza Domain"
                      placeholder="www.ornekfirma.com"
                      value={firmForm.domain_url}
                      onChange={e => setFirmForm({ ...firmForm, domain_url: e.target.value })}
                    />
                    <Input
                      label="Ticimax WS Kodu"
                      type="password"
                      placeholder="UZQ6PXDHSG5ILMWK5BA15WPZWARPCE"
                      value={firmForm.ws_kodu}
                      onChange={e => setFirmForm({ ...firmForm, ws_kodu: e.target.value })}
                      hint="Admin panel → Ayarlar → Web Servis → WS Yetki Kodu"
                    />
                  </div>
                  <div className="actions">
                    <a className="support-link" href="https://wa.me/905000000000" target="_blank" rel="noopener">
                      WhatsApp'tan destek al
                    </a>
                    <Button variant="gradient" onClick={saveFirm} loading={saving}>Kaydet</Button>
                  </div>
                </Card>
              )}

              {/* ── AI Araçları ── */}
              {firm && (
                <Card padding="lg" variant="flat">
                  <h2>AI Görünürlük Araçları</h2>
                  <p className="desc">
                    ChatGPT, Perplexity ve Gemini gibi AI motorlarının mağazanızı tanıması için gerekli dosya ve ayarlar.
                  </p>

                  <div className="ai-tools-grid">
                    {/* llms.txt */}
                    <div className="ai-tool-card">
                      <div className="tool-icon">🤖</div>
                      <div className="tool-body">
                        <strong>llms.txt — AI Sitemapı</strong>
                        <p>ChatGPT, Perplexity ve Google AI&apos;nın mağazanızı tanıması için standart dosya.</p>
                        {firm.llms_txt_generated_at && (
                          <span className="tool-meta">
                            Son üretim: {new Date(firm.llms_txt_generated_at).toLocaleDateString('tr-TR')}
                          </span>
                        )}
                      </div>
                      <Button variant="secondary" size="sm" onClick={downloadLlmsTxt} loading={llmsLoading}>
                        İndir
                      </Button>
                    </div>

                    {/* Marka profili */}
                    <div className="ai-tool-card">
                      <div className="tool-icon">🎯</div>
                      <div className="tool-body">
                        <strong>Marka Profili</strong>
                        <p>AI&apos;nın sizi daha iyi tanıması için 10 soruluk anket. İçerik kalitesini doğrudan etkiler.</p>
                        {firm.firma_profil && Object.keys(firm.firma_profil).length > 0 ? (
                          <Badge tone="success" soft dot>Profil dolu</Badge>
                        ) : (
                          <Badge tone="warning" soft dot>Profil eksik</Badge>
                        )}
                      </div>
                      <Button variant="secondary" size="sm" onClick={() => router.push('/onboarding')}>
                        Düzenle
                      </Button>
                    </div>
                  </div>
                </Card>
              )}
            </>
          )}

          {tab === 'billing' && (
            <Card padding="lg" variant="flat">
              <div className="billing-empty">
                <div className="bill-ico">💳</div>
                <h2>Fatura sistemi yakında</h2>
                <p className="desc">
                  Şu an ücretsiz beta dönemindeyiz. Ödeme entegrasyonu aktifleştiğinde burada
                  kartlarını, faturalarını ve vergi bilgilerini yönetebileceksin.
                </p>
                <Button variant="secondary" onClick={() => router.push('/credits')}>Kredi Paketlerini Gör</Button>
              </div>
            </Card>
          )}
        </div>
      </div>

      <style jsx>{`
        .settings-layout {
          display: grid;
          grid-template-columns: 260px 1fr;
          gap: 24px;
          align-items: start;
        }
        .tabs {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .tab {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 14px;
          background: transparent;
          border: 1px solid transparent;
          border-radius: var(--radius-md);
          cursor: pointer;
          text-align: left;
          transition: all var(--duration-fast) var(--ease-out);
          color: var(--text-secondary);
        }
        .tab:hover {
          background: var(--surface-2);
          color: var(--text-primary);
        }
        .tab.active {
          background: var(--brand-subtle);
          border-color: var(--brand-border);
          color: var(--text-primary);
        }
        .tab-ico {
          font-size: 20px;
          flex-shrink: 0;
        }
        .tab div { display: flex; flex-direction: column; gap: 2px; }
        .tab strong { font-size: var(--text-sm); font-weight: var(--weight-semibold); }
        .tab small { font-size: var(--text-xs); color: var(--text-tertiary); }

        .sec-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 4px;
        }
        h2 { font-size: var(--text-xl); margin: 0 0 4px; }
        .desc {
          color: var(--text-tertiary);
          margin: 0 0 24px;
          font-size: var(--text-sm);
          line-height: 1.55;
        }
        .fields {
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-bottom: 24px;
        }
        .actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
        }
        .support-link {
          font-size: var(--text-sm);
          color: var(--success-text);
          text-decoration: none;
          font-weight: var(--weight-medium);
        }
        .support-link:hover { text-decoration: underline; }

        .billing-empty {
          text-align: center;
          padding: 20px;
        }
        .bill-ico {
          font-size: 2.5rem;
          margin-bottom: 12px;
          opacity: 0.6;
        }

        /* ── AI Tools Grid ── */
        .ai-tools-grid {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .ai-tool-card {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 14px 16px;
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          background: var(--surface-1);
        }
        .tool-icon {
          font-size: 1.5rem;
          flex-shrink: 0;
          width: 36px;
          text-align: center;
        }
        .tool-body {
          flex: 1;
          min-width: 0;
        }
        .tool-body strong {
          display: block;
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          margin-bottom: 2px;
        }
        .tool-body p {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin: 0 0 4px;
          line-height: 1.4;
        }
        .tool-meta {
          font-size: var(--text-xs);
          color: var(--text-quaternary);
        }

        .tab-body {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        @media (max-width: 800px) {
          .settings-layout { grid-template-columns: 1fr; }
          .tabs { flex-direction: row; overflow-x: auto; }
          .tab { flex-shrink: 0; }
          .ai-tool-card { flex-wrap: wrap; }
        }
      `}</style>
    </>
  )
}
