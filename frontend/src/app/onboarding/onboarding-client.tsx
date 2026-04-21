'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Input, Badge, ToastProvider, useToast } from '@/components/ui'

const FIRMA_SORULARI = [
  {
    key: 'ana_kategori',
    soru: 'Markanızın ana ürün kategorisi nedir?',
    tip: 'select',
    secenekler: [
      { label: 'İç Giyim (sütyen, külot, pijama)', value: 'ic_giyim' },
      { label: 'Dış Giyim (elbise, bluz, pantolon)', value: 'kadin_giyim' },
      { label: 'Ayakkabı & Çanta', value: 'ayakkabi_canta' },
      { label: 'Takı & Aksesuar (gümüş, altın, bijuteri)', value: 'taki_aksesuar' },
      { label: 'Elektronik & Teknoloji', value: 'elektronik' },
      { label: 'Ev & Dekor', value: 'ev_dekor' },
      { label: 'Spor & Outdoor', value: 'spor' },
      { label: 'Hırdavat & El Aletleri', value: 'hirdavat' },
      { label: 'Diğer', value: 'diger' },
    ],
  },
  {
    key: 'hedef_kitle',
    soru: 'Hedef müşteri kitlenizi kısaca tanımlayın',
    tip: 'text',
    placeholder: 'Örn: 25-40 yaş arası çalışan kadın, kalite ve konforu önceliklendirir',
    hint: 'AI içerik yazarı bu bilgiyi ikna edici içerik için kullanır',
  },
  {
    key: 'deger_onerisi',
    soru: 'Markanızın müşteriye verdiği ana değer nedir?',
    tip: 'select',
    secenekler: [
      { label: 'Uygun fiyat / bütçe dostu', value: 'fiyat' },
      { label: 'Yüksek kalite / uzun ömürlü', value: 'kalite' },
      { label: 'Türkiye üretimi / yerli marka', value: 'yerli' },
      { label: 'El yapımı / özgün tasarım', value: 'el_yapimi' },
      { label: 'Sürdürülebilir / çevre dostu', value: 'surdurulebilir' },
      { label: 'Geniş beden aralığı / kapsayıcı', value: 'kapsayici' },
      { label: 'Lüks & premium segment', value: 'luks' },
    ],
  },
  {
    key: 'en_cok_satan',
    soru: 'En çok sattığınız ürün grubu hangisi?',
    tip: 'text',
    placeholder: 'Örn: Pamuklu sütyen setleri, yazlık elbiseler, gümüş kolye',
  },
  {
    key: 'rakip_farki',
    soru: 'Sizi rakiplerden ayıran en önemli özellik nedir?',
    tip: 'text',
    placeholder: 'Örn: %100 Türk pamuğu kullanımı, büyük beden uzmanlığı, el nakışı detaylar',
  },
  {
    key: 'marka_tonu',
    soru: 'Markanızın iletişim tonu nasıl olmalı?',
    tip: 'select',
    secenekler: [
      { label: 'Samimi ve sıcak (arkadaş gibi)', value: 'samimi' },
      { label: 'Profesyonel ve güven verici', value: 'profesyonel' },
      { label: 'Lüks ve sofistike', value: 'luks' },
      { label: 'Genç ve enerjik', value: 'genc' },
      { label: 'Minimal ve sade', value: 'minimal' },
    ],
  },
  {
    key: 'uretim_yeri',
    soru: 'Ürünleriniz nereden temin ediliyor?',
    tip: 'select',
    secenekler: [
      { label: 'Türkiye üretimi (kendi fabrika/atölye)', value: 'turkiye' },
      { label: 'Türkiye üretimi (fason/tedarikçi)', value: 'turkiye_fason' },
      { label: 'İthal ürün', value: 'ithal' },
      { label: 'El yapımı (bireysel üretim)', value: 'el_yapimi' },
      { label: 'Karma (yerli + ithal)', value: 'karma' },
    ],
  },
  {
    key: 'musteri_kriteri',
    soru: 'Müşterileriniz için en önemli satın alma kriteri nedir?',
    tip: 'select',
    secenekler: [
      { label: 'Fiyat (uygun/indirimli)', value: 'fiyat' },
      { label: 'Kalite (uzun ömürlü, dayanıklı)', value: 'kalite' },
      { label: 'Hız (hızlı kargo, stokta hazır)', value: 'hiz' },
      { label: 'Marka güveni (tanınan isim)', value: 'guven' },
      { label: 'Çeşitlilik (geniş ürün kataloğu)', value: 'cesitlilik' },
    ],
  },
  {
    key: 'platformlar',
    soru: 'Hangi platformlarda aktif satış yapıyorsunuz?',
    tip: 'checkbox',
    secenekler: [
      { label: 'Ticimax (kendi site)', value: 'ticimax' },
      { label: 'Trendyol', value: 'trendyol' },
      { label: 'Hepsiburada', value: 'hepsiburada' },
      { label: 'N11', value: 'n11' },
      { label: 'Amazon Türkiye', value: 'amazon' },
      { label: 'Instagram/Sosyal medya', value: 'sosyal_medya' },
    ],
  },
  {
    key: 'marka_hikayesi',
    soru: 'Markanızın kısa hikayesi veya vizyonu nedir?',
    tip: 'textarea',
    placeholder: 'Örn: 2015\'te İstanbul\'da kurulan markamız, Türk kadınına konforlu ve kaliteli iç giyim sunmayı hedefler...',
    hint: 'Max 200 karakter — AI\'nın sizi tanıması için en kritik alan',
    maxLen: 200,
  },
]

interface Existing {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  firma_profil?: Record<string, unknown> | null
}

export default function OnboardingClient({ userId, existing }: { userId: string; existing: Existing | null }) {
  return (
    <ToastProvider>
      <Inner userId={userId} existing={existing} />
    </ToastProvider>
  )
}

function Inner({ userId, existing }: { userId: string; existing: Existing | null }) {
  const hasExisting = !!existing?.company_name
  const hasWs = !!existing?.ws_kodu
  const hasProfil = !!(existing?.firma_profil && Object.keys(existing.firma_profil).length > 0)
  const [step, setStep] = useState(hasProfil ? 3 : hasWs ? 2 : hasExisting ? 1 : 0)

  const [form, setForm] = useState({
    company_name: existing?.company_name || '',
    domain_url: existing?.domain_url || '',
    ws_kodu: existing?.ws_kodu || '',
  })

  // Profil anketi cevapları
  const [profil, setProfil] = useState<Record<string, unknown>>(
    (existing?.firma_profil as Record<string, unknown>) || {}
  )
  const [saving, setSaving] = useState(false)
  const [orgId, setOrgId] = useState(existing?.id || '')
  const router = useRouter()
  const supabase = createClient()
  const toast = useToast()

  const goNext = () => setStep(s => Math.min(3, s + 1))
  const goBack = () => setStep(s => Math.max(0, s - 1))

  const saveStep0 = async () => {
    if (!form.company_name.trim()) return toast.show('Firma adı gerekli', 'warning')
    setSaving(true)
    if (existing) {
      await supabase.from('organizations').update({
        company_name: form.company_name,
        domain_url: form.domain_url || null,
      }).eq('id', existing.id)
      setOrgId(existing.id)
    } else {
      const { data } = await supabase.from('organizations').insert({
        user_id: userId,
        company_name: form.company_name,
        domain_url: form.domain_url || null,
      }).select('id').single()
      if (data?.id) setOrgId(data.id)
    }
    setSaving(false)
    goNext()
  }

  const saveStep1 = async () => {
    if (!form.ws_kodu.trim()) return toast.show('WS kodu gerekli', 'warning')
    setSaving(true)
    await supabase.from('organizations').update({ ws_kodu: form.ws_kodu }).eq('user_id', userId)
    setSaving(false)
    goNext()
  }

  const saveStep2 = async () => {
    const required = ['ana_kategori', 'hedef_kitle', 'marka_tonu']
    const missing = required.find(k => !profil[k])
    if (missing) return toast.show('Lütfen zorunlu soruları doldurun', 'warning')
    setSaving(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/firma-profil`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ organization_id: orgId, profil }),
      })
      if (!res.ok) throw new Error('Kayıt hatası')
      toast.show('Firma profili kaydedildi', 'success')
      goNext()
    } catch {
      toast.show('Profil kaydedilemedi, devam edebilirsiniz', 'warning')
      goNext()
    } finally {
      setSaving(false)
    }
  }

  const finish = () => {
    toast.show('Kurulum tamamlandı!', 'success')
    router.push('/seo')
  }

  const setProfilField = (key: string, val: unknown) =>
    setProfil(p => ({ ...p, [key]: val }))

  const toggleCheckbox = (key: string, val: string) => {
    const cur = (profil[key] as string[]) || []
    const next = cur.includes(val) ? cur.filter(v => v !== val) : [...cur, val]
    setProfilField(key, next)
  }

  const STEPS = ['Firma Bilgileri', 'Ticimax Bağlantısı', 'Marka Profili', 'Tamamlandı']

  return (
    <div className="onboarding-page">
      <div className="onb-container">
        <header className="onb-header">
          <div className="brand">
            <div className="brand-mark">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M3 13L8 3L13 13H3Z" fill="white" />
              </svg>
            </div>
            <span>Pixra</span>
          </div>
          <Badge tone="brand" soft>İlk 10 analiz hediye</Badge>
        </header>

        <div className="steps-indicator">
          {STEPS.map((label, i) => (
            <div key={i} className={`step-dot ${step >= i ? 'active' : ''} ${step === i ? 'current' : ''}`}>
              <span>{i + 1}</span>
              <label>{label}</label>
            </div>
          ))}
        </div>

        {/* ── Adım 0: Firma bilgileri ── */}
        {step === 0 && (
          <Card variant="magic" padding="lg">
            <h2>Firma bilgilerini gir</h2>
            <p className="desc">Bu bilgiler mağazanı tanımak ve doğru içerik üretmek için kullanılır.</p>
            <div className="fields">
              <Input
                label="Firma Adı"
                placeholder="Örn: Lola of Shine"
                value={form.company_name}
                onChange={e => setForm({ ...form, company_name: e.target.value })}
                required
              />
              <Input
                label="Mağaza Domain"
                placeholder="www.ornekfirma.com"
                value={form.domain_url}
                onChange={e => setForm({ ...form, domain_url: e.target.value })}
                hint="Opsiyonel — SEO içerik üretiminde kullanılır."
              />
            </div>
            <div className="actions">
              <Button variant="ghost" onClick={() => router.push('/')}>İptal</Button>
              <Button variant="gradient" onClick={saveStep0} loading={saving}>Devam Et →</Button>
            </div>
          </Card>
        )}

        {/* ── Adım 1: Ticimax WS kodu ── */}
        {step === 1 && (
          <div className="split">
            <Card padding="lg">
              <h2>Ticimax WS Kodunu Gir</h2>
              <p className="desc">Ticimax panelinden aldığın WS (Web Servis) yetki kodu.</p>
              <Input
                label="WS Kodu"
                placeholder="UZQ6PXDHSG5ILMWK5BA15WPZWARPCE"
                value={form.ws_kodu}
                onChange={e => setForm({ ...form, ws_kodu: e.target.value })}
                required
              />
              <div className="actions">
                <Button variant="ghost" onClick={goBack}>← Geri</Button>
                <Button variant="gradient" onClick={saveStep1} loading={saving}>Devam Et →</Button>
              </div>
            </Card>
            <Card variant="flat" padding="lg">
              <h3>WS Kodunu nasıl bulurum?</h3>
              <ol className="guide">
                <li>Ticimax admin paneline gir (admin.ticimax.com)</li>
                <li>Sol menüden <strong>Ayarlar → Web Servis</strong></li>
                <li><strong>WS Yetki Kodu</strong> kopyala</li>
                <li>Aktif değilse Ticimax destekten aktivasyon iste</li>
              </ol>
              <div className="support">
                <span>Takıldın mı?</span>
                <a href="https://wa.me/905000000000" target="_blank" rel="noopener">WhatsApp'tan destek al</a>
              </div>
            </Card>
          </div>
        )}

        {/* ── Adım 2: Marka profil anketi (10 soru) ── */}
        {step === 2 && (
          <Card padding="lg">
            <h2>Markanızı tanıyalım</h2>
            <p className="desc">
              Bu bilgiler AI&apos;nın sizin için daha doğru, dönüşüm odaklı içerik üretmesini sağlar.
              <strong> Yıldızlı alanlar zorunludur.</strong>
            </p>
            <div className="profil-grid">
              {FIRMA_SORULARI.map((soru, idx) => (
                <div key={soru.key} className="soru-blok">
                  <label className="soru-label">
                    <span className="soru-no">{idx + 1}</span>
                    {soru.soru}
                    {['ana_kategori', 'hedef_kitle', 'marka_tonu'].includes(soru.key) && (
                      <span className="required-star"> *</span>
                    )}
                  </label>

                  {soru.hint && <p className="soru-hint">{soru.hint}</p>}

                  {soru.tip === 'select' && (
                    <div className="radio-group">
                      {soru.secenekler!.map(opt => (
                        <label key={opt.value} className={`radio-opt ${profil[soru.key] === opt.value ? 'selected' : ''}`}>
                          <input
                            type="radio"
                            name={soru.key}
                            value={opt.value}
                            checked={profil[soru.key] === opt.value}
                            onChange={() => setProfilField(soru.key, opt.value)}
                          />
                          {opt.label}
                        </label>
                      ))}
                    </div>
                  )}

                  {soru.tip === 'checkbox' && (
                    <div className="radio-group">
                      {soru.secenekler!.map(opt => {
                        const checked = ((profil[soru.key] as string[]) || []).includes(opt.value)
                        return (
                          <label key={opt.value} className={`radio-opt ${checked ? 'selected' : ''}`}>
                            <input
                              type="checkbox"
                              value={opt.value}
                              checked={checked}
                              onChange={() => toggleCheckbox(soru.key, opt.value)}
                            />
                            {opt.label}
                          </label>
                        )
                      })}
                    </div>
                  )}

                  {soru.tip === 'text' && (
                    <input
                      className="text-input"
                      type="text"
                      placeholder={soru.placeholder}
                      value={(profil[soru.key] as string) || ''}
                      onChange={e => setProfilField(soru.key, e.target.value)}
                    />
                  )}

                  {soru.tip === 'textarea' && (
                    <>
                      <textarea
                        className="textarea-input"
                        placeholder={soru.placeholder}
                        maxLength={soru.maxLen}
                        rows={3}
                        value={(profil[soru.key] as string) || ''}
                        onChange={e => setProfilField(soru.key, e.target.value)}
                      />
                      <span className="char-count">
                        {((profil[soru.key] as string) || '').length} / {soru.maxLen}
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>

            <div className="actions">
              <Button variant="ghost" onClick={goBack}>← Geri</Button>
              <Button variant="gradient" onClick={saveStep2} loading={saving}>
                Profili Kaydet →
              </Button>
            </div>
          </Card>
        )}

        {/* ── Adım 3: Tamamlandı ── */}
        {step === 3 && (
          <Card variant="magic" padding="lg">
            <div className="success">
              <div className="success-icon">🎉</div>
              <h2>Kurulum tamamlandı!</h2>
              <p className="desc">
                Harika — markanızı tanıdık. Artık Pixra, sizin için
                <strong> dönüşüm odaklı, semantik zengin</strong> içerik üretecek.
                Hesabınıza <strong>10 ücretsiz ürün analizi</strong> tanımlandı.
              </p>
              <Button variant="gradient" size="lg" onClick={finish}>
                İlk Analizi Başlat →
              </Button>
            </div>
          </Card>
        )}
      </div>

      <style jsx>{`
        .onboarding-page {
          min-height: 100vh;
          background: radial-gradient(ellipse at top, rgba(99, 102, 241, 0.08), transparent 60%),
                      var(--surface-0);
          padding: 48px 20px;
        }
        .onb-container {
          max-width: 860px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 32px;
        }
        .onb-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: var(--text-lg);
          font-weight: var(--weight-bold);
        }
        .brand-mark {
          width: 28px;
          height: 28px;
          background: var(--brand-gradient);
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .steps-indicator {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 24px;
        }
        .step-dot {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          opacity: 0.4;
          transition: opacity var(--duration-base) var(--ease-out);
        }
        .step-dot.active { opacity: 1; }
        .step-dot span {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          border: 2px solid var(--border-default);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: var(--weight-semibold);
          font-size: var(--text-sm);
          background: var(--surface-2);
        }
        .step-dot.active span {
          background: var(--brand-gradient);
          color: #fff;
          border-color: transparent;
        }
        .step-dot.current span { box-shadow: 0 0 0 4px var(--brand-subtle); }
        .step-dot label {
          font-size: 0.65rem;
          color: var(--text-tertiary);
          font-weight: var(--weight-medium);
          white-space: nowrap;
        }

        h2 { font-size: var(--text-2xl); margin: 0 0 8px; }
        h3 { font-size: var(--text-lg); margin: 0 0 12px; }
        .desc {
          color: var(--text-tertiary);
          margin: 0 0 24px;
          font-size: var(--text-sm);
          line-height: 1.55;
        }
        .desc strong { color: var(--brand-text); font-weight: var(--weight-semibold); }

        .fields { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }
        .actions { display: flex; justify-content: space-between; gap: 8px; margin-top: 24px; }
        .split { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }

        .guide {
          display: flex; flex-direction: column; gap: 10px;
          padding-left: 20px; margin: 0 0 20px;
          color: var(--text-secondary); font-size: var(--text-sm); line-height: 1.55;
        }
        .guide li { padding-left: 4px; }
        .guide strong { color: var(--text-primary); }
        .support {
          display: flex; flex-direction: column; gap: 4px;
          padding: 12px 14px; background: var(--surface-2);
          border-radius: var(--radius-md); font-size: var(--text-sm); color: var(--text-tertiary);
        }
        .support a { color: var(--success-text); font-weight: var(--weight-semibold); text-decoration: none; }
        .support a:hover { text-decoration: underline; }

        /* ── Profil Anketi ── */
        .profil-grid {
          display: flex;
          flex-direction: column;
          gap: 28px;
          margin-bottom: 8px;
        }
        .soru-blok {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .soru-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
          display: flex;
          align-items: baseline;
          gap: 8px;
        }
        .soru-no {
          min-width: 22px;
          height: 22px;
          background: var(--brand-subtle);
          color: var(--brand-text);
          border-radius: 50%;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: var(--weight-bold);
        }
        .required-star { color: var(--danger-text); }
        .soru-hint { font-size: var(--text-xs); color: var(--text-tertiary); margin: 0; }

        .radio-group {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .radio-opt {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border: 1px solid var(--border-default);
          border-radius: var(--radius-full);
          font-size: var(--text-sm);
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
          background: var(--surface-1);
          color: var(--text-secondary);
          user-select: none;
        }
        .radio-opt:hover { border-color: var(--brand-border); color: var(--text-primary); }
        .radio-opt.selected {
          background: var(--brand-subtle);
          border-color: var(--brand-border);
          color: var(--brand-text);
          font-weight: var(--weight-medium);
        }
        .radio-opt input { display: none; }

        .text-input {
          width: 100%;
          padding: 10px 12px;
          background: var(--surface-1);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-md);
          color: var(--text-primary);
          font-size: var(--text-sm);
          transition: border-color var(--duration-fast);
          box-sizing: border-box;
        }
        .text-input:focus { outline: none; border-color: var(--brand-border); }
        .textarea-input {
          width: 100%;
          padding: 10px 12px;
          background: var(--surface-1);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-md);
          color: var(--text-primary);
          font-size: var(--text-sm);
          resize: vertical;
          transition: border-color var(--duration-fast);
          box-sizing: border-box;
          font-family: inherit;
        }
        .textarea-input:focus { outline: none; border-color: var(--brand-border); }
        .char-count { font-size: var(--text-xs); color: var(--text-quaternary); align-self: flex-end; }

        .success { text-align: center; padding: 20px; }
        .success-icon { font-size: 3rem; margin-bottom: 12px; }

        @media (max-width: 700px) {
          .split { grid-template-columns: 1fr; }
          .steps-indicator { gap: 12px; }
        }
      `}</style>
    </div>
  )
}
