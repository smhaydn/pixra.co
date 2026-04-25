'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'
import { Button, Card, Input, Badge, useToast } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface SectorOption { id: string; display_name: string }

interface Firm {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  gemini_api_key: string | null
  sector_id: string | null
  firma_profil?: Record<string, unknown> | null
  llms_txt_generated_at?: string | null
}

interface GscStatus {
  connected: boolean
  property_url?: string
  connected_at?: string
  sites_count?: number
}

type Tab = 'profile' | 'firm' | 'integrations' | 'billing'

export default function SettingsClient({ user, firm, readOnly = false }: { user: User; firm: Firm | null; readOnly?: boolean }) {
  const searchParams = useSearchParams()
  const [tab, setTab] = useState<Tab>(() => {
    const t = searchParams?.get('tab')
    if (t === 'integrations') return 'integrations'
    return 'profile'
  })
  const [saving, setSaving] = useState(false)
  const [logouting, setLogouting] = useState(false)
  const toast = useToast()
  const router = useRouter()
  const supabase = createClient()

  const [profile, setProfile] = useState({
    full_name: user.user_metadata?.full_name || '',
    email: user.email || '',
  })
  const [sectors, setSectors] = useState<SectorOption[]>([])
  const [firmForm, setFirmForm] = useState({
    company_name: firm?.company_name || '',
    domain_url: firm?.domain_url || '',
    ws_kodu: firm?.ws_kodu || '',
    gemini_api_key: firm?.gemini_api_key || '',
    sector_id: firm?.sector_id || '',
  })

  // Google OAuth credentials (per-org, saved to firma_profil.__google_oauth__)
  const googleOAuthRaw = firm?.firma_profil?.__google_oauth__ as Record<string, string> | undefined
  const [googleOAuth, setGoogleOAuth] = useState({
    client_id: googleOAuthRaw?.client_id || '',
    client_secret: googleOAuthRaw?.client_secret || '',
  })
  const [savingOAuth, setSavingOAuth] = useState(false)

  // GSC state
  const [gscStatus, setGscStatus] = useState<GscStatus | null>(null)
  const [gscLoading, setGscLoading] = useState(false)
  const [gscConnecting, setGscConnecting] = useState(false)
  const [gscDisconnecting, setGscDisconnecting] = useState(false)

  const loadGscStatus = useCallback(async () => {
    if (!firm) return
    setGscLoading(true)
    try {
      const res = await fetch(`${API}/api/integrations/gsc/status?org_id=${firm.id}`)
      if (res.ok) setGscStatus(await res.json())
    } catch { /* best-effort */ }
    setGscLoading(false)
  }, [firm])

  useEffect(() => {
    supabase.from('sectors').select('id,display_name').eq('aktif', true).order('display_name')
      .then(({ data }) => { if (data) setSectors(data) })
    // GSC callback sonrası bildirim
    const gscParam = searchParams?.get('gsc')
    if (gscParam === 'connected') {
      toast.show('Google Search Console başarıyla bağlandı! 🎉', 'success')
      loadGscStatus()
    } else if (gscParam === 'error') {
      toast.show('GSC bağlantısı başarısız oldu, tekrar deneyin.', 'error')
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (tab === 'integrations' && !gscStatus && !gscLoading) {
      loadGscStatus()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

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
      gemini_api_key: firmForm.gemini_api_key || null,
      sector_id: firmForm.sector_id || null,
    }).eq('id', firm.id)
    setSaving(false)
    toast.show('Firma bilgileri güncellendi', 'success')
    router.refresh()
  }

  const connectGsc = async () => {
    if (!firm) return
    setGscConnecting(true)
    try {
      const res = await fetch(`${API}/api/integrations/gsc/auth-url?org_id=${firm.id}`)
      if (!res.ok) throw new Error('URL alınamadı')
      const { url } = await res.json()
      window.location.href = url   // Google OAuth sayfasına yönlendir
    } catch (err) {
      toast.show(`GSC bağlantısı başlatılamadı: ${String(err)}`, 'error')
      setGscConnecting(false)
    }
  }

  const saveGoogleOAuth = async () => {
    if (!firm) return
    setSavingOAuth(true)
    // Mevcut firma_profil'i koru, sadece __google_oauth__ güncelle
    const currentProfil = (firm.firma_profil as Record<string, unknown>) || {}
    const merged = {
      ...currentProfil,
      __google_oauth__: {
        client_id: googleOAuth.client_id.trim(),
        client_secret: googleOAuth.client_secret.trim(),
      },
    }
    await supabase.from('organizations').update({ firma_profil: merged }).eq('id', firm.id)
    setSavingOAuth(false)
    toast.show('Google OAuth bilgileri kaydedildi', 'success')
  }

  const disconnectGsc = async () => {
    if (!firm || !confirm('GSC bağlantısını kaldırmak istediğinizden emin misiniz?')) return
    setGscDisconnecting(true)
    try {
      await fetch(`${API}/api/integrations/gsc/disconnect?org_id=${firm.id}`, { method: 'DELETE' })
      setGscStatus({ connected: false })
      toast.show('GSC bağlantısı kaldırıldı', 'success')
    } catch {
      toast.show('Kaldırılamadı, tekrar deneyin', 'error')
    }
    setGscDisconnecting(false)
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
          <button className={`tab ${tab === 'integrations' ? 'active' : ''}`} onClick={() => setTab('integrations')}>
            <span className="tab-ico">🔗</span>
            <div>
              <strong>Entegrasyonlar</strong>
              <small>GSC, Analytics bağlantıları</small>
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
                    {sectors.length > 0 && (
                      <div>
                        <label style={{ display: 'block', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', marginBottom: 8, color: 'var(--text-primary)' }}>
                          Sektör
                          <span style={{ color: 'var(--text-tertiary)', fontWeight: 'normal', marginLeft: 6, fontSize: 'var(--text-xs)' }}>— AI bu sektöre özel içerik üretir</span>
                        </label>
                        <select
                          value={firmForm.sector_id}
                          onChange={e => setFirmForm({ ...firmForm, sector_id: e.target.value })}
                          style={{
                            width: '100%', padding: '10px 12px',
                            background: 'var(--surface-1)', border: '1px solid var(--border-default)',
                            borderRadius: 'var(--radius-md)', color: 'var(--text-primary)',
                            fontSize: 'var(--text-sm)', appearance: 'none',
                          }}
                        >
                          <option value="">— Sektör seçin —</option>
                          {sectors.map(s => (
                            <option key={s.id} value={s.id}>{s.display_name}</option>
                          ))}
                        </select>
                      </div>
                    )}
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

          {tab === 'integrations' && (
            <>
              {/* ── Google OAuth Credentials ── */}
              <Card padding="lg" variant="flat">
                <div className="sec-head">
                  <h2>Google OAuth Kimlik Bilgileri</h2>
                  {googleOAuth.client_id ? (
                    <Badge tone="success" dot>Ayarlandı</Badge>
                  ) : (
                    <Badge tone="warning" dot>Eksik</Badge>
                  )}
                </div>
                <p className="desc">
                  Google Search Console bağlantısı için kendi Google Cloud projenizden OAuth 2.0 kimlik bilgilerinizi girin.
                  Bu bilgiler şifreli saklanır ve yalnızca GSC bağlantısı için kullanılır.
                </p>
                <div className="fields">
                  <Input
                    label="Client ID"
                    placeholder="123456789-abc.apps.googleusercontent.com"
                    value={googleOAuth.client_id}
                    onChange={e => setGoogleOAuth({ ...googleOAuth, client_id: e.target.value })}
                    hint="Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID"
                  />
                  <Input
                    label="Client Secret"
                    type="password"
                    placeholder="GOCSPX-..."
                    value={googleOAuth.client_secret}
                    onChange={e => setGoogleOAuth({ ...googleOAuth, client_secret: e.target.value })}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <a
                    href="https://console.cloud.google.com/apis/credentials"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="support-link"
                  >
                    Google Cloud Console →
                  </a>
                  <Button
                    variant="gradient"
                    size="sm"
                    onClick={saveGoogleOAuth}
                    loading={savingOAuth}
                    disabled={!googleOAuth.client_id || !googleOAuth.client_secret}
                  >
                    Kaydet
                  </Button>
                </div>
              </Card>

              <Card padding="lg">
                <div className="sec-head">
                  <h2>Google Search Console</h2>
                  {gscStatus?.connected ? (
                    <Badge tone="success" dot>Bağlı</Badge>
                  ) : (
                    <Badge tone="neutral" dot>Bağlı değil</Badge>
                  )}
                </div>
                <p className="desc">
                  GSC bağlantısı ile mağazanızın gerçek arama sorgularını sisteme entegre edin.
                  AI içerik üretimi ve sektör RAG verisi bu keyword&apos;lerle otomatik güçlenir.
                </p>

                {gscLoading ? (
                  <p style={{ color: 'var(--text-tertiary)', fontSize: 'var(--text-sm)' }}>Durum kontrol ediliyor...</p>
                ) : gscStatus?.connected ? (
                  <div className="integration-card connected">
                    <div className="int-icon">✅</div>
                    <div className="int-body">
                      <strong>Search Console Bağlı</strong>
                      {gscStatus.property_url && (
                        <p>Mülk: <code>{gscStatus.property_url}</code></p>
                      )}
                      {gscStatus.connected_at && (
                        <span className="tool-meta">
                          Bağlandı: {new Date(gscStatus.connected_at).toLocaleDateString('tr-TR')}
                        </span>
                      )}
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={disconnectGsc}
                      loading={gscDisconnecting}
                    >
                      Bağlantıyı Kaldır
                    </Button>
                  </div>
                ) : (
                  <div className="integration-card">
                    <div className="int-icon">📊</div>
                    <div className="int-body">
                      <strong>Henüz bağlı değil</strong>
                      <p>Google hesabınızla oturum açıp Search Console erişimine izin verin.</p>
                      {!googleOAuth.client_id && (
                        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--error-text)' }}>
                          ⚠️ Önce yukarıdan Google OAuth bilgilerini girin.
                        </p>
                      )}
                      {googleOAuth.client_id && (
                        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-quaternary)' }}>
                          Yalnızca <strong>okuma</strong> yetkisi istenir — hiçbir değişiklik yapılmaz.
                        </p>
                      )}
                    </div>
                    <Button
                      variant="gradient"
                      size="sm"
                      onClick={connectGsc}
                      loading={gscConnecting}
                      disabled={!firm || !googleOAuth.client_id}
                    >
                      Google ile Bağla
                    </Button>
                  </div>
                )}
              </Card>

              <Card padding="lg" variant="flat">
                <h2>Yakında</h2>
                <p className="desc">Google Analytics 4, Meta Pixel ve daha fazla entegrasyon geliyor.</p>
                <div className="coming-soon-list">
                  {[
                    { icon: '📈', label: 'Google Analytics 4', status: 'Geliştiriliyor' },
                    { icon: '🎯', label: 'Meta Pixel / CAPI', status: 'Planlandı' },
                    { icon: '🛒', label: 'Kritik Ürün Takibi', status: 'Planlandı' },
                  ].map(item => (
                    <div key={item.label} className="coming-item">
                      <span className="int-icon">{item.icon}</span>
                      <span className="int-body"><strong>{item.label}</strong></span>
                      <Badge tone="neutral" soft>{item.status}</Badge>
                    </div>
                  ))}
                </div>
              </Card>
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

        /* ── Entegrasyon kartı ── */
        .integration-card {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 16px;
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          background: var(--surface-1);
        }
        .integration-card.connected {
          border-color: rgba(34,197,94,0.3);
          background: rgba(34,197,94,0.04);
        }
        .int-icon {
          font-size: 1.5rem;
          flex-shrink: 0;
          width: 36px;
          text-align: center;
        }
        .int-body {
          flex: 1;
          min-width: 0;
        }
        .int-body strong {
          display: block;
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          margin-bottom: 2px;
        }
        .int-body p {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin: 2px 0;
          line-height: 1.4;
        }
        .int-body code {
          font-size: var(--text-xs);
          background: var(--surface-2);
          padding: 1px 5px;
          border-radius: 4px;
        }
        .coming-soon-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-top: 12px;
        }
        .coming-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          background: var(--surface-1);
          opacity: 0.7;
        }

        @media (max-width: 800px) {
          .settings-layout { grid-template-columns: 1fr; }
          .tabs { flex-direction: row; overflow-x: auto; }
          .tab { flex-shrink: 0; }
          .ai-tool-card { flex-wrap: wrap; }
          .integration-card { flex-wrap: wrap; }
        }
      `}</style>
    </>
  )
}
