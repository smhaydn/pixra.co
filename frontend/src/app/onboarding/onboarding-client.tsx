'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Input, Badge, ToastProvider, useToast } from '@/components/ui'

interface SectorOption {
  id: string
  slug: string
  display_name: string
}

const FIRMA_SORULARI = [
  {
    key: 'ana_kategori',
    soru: 'Markanızın ana ürün kategorisi nedir?',
    tip: 'checkbox',
    hint: 'Birden fazla seçebilirsiniz',
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
    soru: 'Markanızın müşteriye verdiği değerler nelerdir?',
    tip: 'checkbox',
    hint: 'Birden fazla seçebilirsiniz',
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
    key: 'marka_gucu',
    soru: 'Markanızın en güçlü yanları nelerdir?',
    tip: 'checkbox',
    hint: 'Birden fazla seçebilirsiniz — AI içeriğinizde bunları öne çıkarır',
    secenekler: [
      { label: 'Özgün / kendi tasarımı ürünler', value: 'ozgun_tasarim' },
      { label: 'Güçlü müşteri hizmetleri', value: 'musteri_hizmetleri' },
      { label: 'Hızlı & güvenilir teslimat', value: 'hizli_teslimat' },
      { label: 'Özel ambalaj / unboxing deneyimi', value: 'ozel_ambalaj' },
      { label: 'Sadık / geri dönen müşteri kitlesi', value: 'sadik_musteri' },
      { label: 'Güçlü sosyal medya varlığı', value: 'sosyal_medya_varligi' },
      { label: 'Ödül / sertifika / basın haberi', value: 'odul_sertifika' },
      { label: 'Geniş ürün çeşitliliği', value: 'genis_cesit' },
    ],
  },
  {
    key: 'musteri_kriteri',
    soru: 'Müşterileriniz için önemli satın alma kriterleri nelerdir?',
    tip: 'checkbox',
    hint: 'Birden fazla seçebilirsiniz',
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
    soru: 'Markanızın hikayesi veya vizyonu nedir?',
    tip: 'textarea',
    placeholder: 'Örn: 2015\'te İstanbul\'da kurulan markamız, Türk kadınına konforlu ve kaliteli iç giyim sunmayı hedefler. Müşteri memnuniyetini her şeyin önünde tutarak...',
    hint: 'Min 200 — Max 5000 karakter. AI\'nın sizi tanıması için en kritik alan.',
    minLen: 200,
    maxLen: 5000,
  },
]

interface Existing {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string | null
  sector_id: string | null
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
  const hasKurucu = !!(existing?.firma_profil && (existing.firma_profil as Record<string, unknown>)['kurucu_adi'])
  const [step, setStep] = useState(hasKurucu ? 4 : hasProfil ? 3 : hasWs ? 2 : hasExisting ? 1 : 0)

  const [sectors, setSectors] = useState<SectorOption[]>([])
  const [form, setForm] = useState({
    company_name: existing?.company_name || '',
    domain_url: existing?.domain_url || '',
    ws_kodu: existing?.ws_kodu || '',
    sector_id: existing?.sector_id || '',
  })

  useEffect(() => {
    supabase.from('sectors').select('id,slug,display_name').eq('aktif', true).order('display_name')
      .then(({ data }) => { if (data) setSectors(data) })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const [profil, setProfil] = useState<Record<string, unknown>>(
    (existing?.firma_profil as Record<string, unknown>) || {}
  )
  const [kurucu, setKurucu] = useState<Record<string, string>>(
    ((existing?.firma_profil as Record<string, unknown>)?.['kurucu'] as Record<string, string>) || {}
  )
  const [saving, setSaving] = useState(false)
  const [orgId, setOrgId] = useState(existing?.id || '')
  const router = useRouter()
  const supabase = createClient()
  const toast = useToast()

  const goNext = () => setStep(s => Math.min(4, s + 1))
  const goBack = () => setStep(s => Math.max(0, s - 1))

  const saveStep0 = async () => {
    if (!form.company_name.trim()) return toast.show('Firma adı gerekli', 'warning')
    if (!form.sector_id) return toast.show('Lütfen sektör seçin', 'warning')
    setSaving(true)
    const orgPayload = {
      company_name: form.company_name,
      domain_url: form.domain_url || null,
      sector_id: form.sector_id || null,
    }
    if (existing) {
      await supabase.from('organizations').update(orgPayload).eq('id', existing.id)
      setOrgId(existing.id)
    } else {
      const { data } = await supabase.from('organizations').insert({
        user_id: userId,
        ...orgPayload,
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
    const missing = required.find(k => {
      const v = profil[k]
      return !v || (Array.isArray(v) && v.length === 0)
    })
    if (missing) return toast.show('Lütfen zorunlu soruları doldurun', 'warning')
    const hikaye = (profil['marka_hikayesi'] as string) || ''
    if (hikaye.length > 0 && hikaye.length < 200)
      return toast.show('Marka hikayesi en az 200 karakter olmalı', 'warning')
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

  const saveStep3 = async () => {
    if (!kurucu.kurucu_adi?.trim()) return toast.show('Kurucu adı gerekli', 'warning')
    setSaving(true)
    try {
      const merged = { ...profil, kurucu }
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/firma-profil`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ organization_id: orgId, profil: merged }),
      })
      if (!res.ok) throw new Error()
      toast.show('Kurucu bilgileri kaydedildi', 'success')
      goNext()
    } catch {
      toast.show('Kaydedilemedi, devam edebilirsiniz', 'warning')
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

  const setKurucuField = (key: string, val: string) =>
    setKurucu(k => ({ ...k, [key]: val }))

  const toggleCheckbox = (key: string, val: string) => {
    const cur = (profil[key] as string[]) || []
    const next = cur.includes(val) ? cur.filter(v => v !== val) : [...cur, val]
    setProfilField(key, next)
  }

  const STEPS = ['Firma Bilgileri', 'Ticimax Bağlantısı', 'Marka Profili', 'Kurucu & Hikaye', 'Tamamlandı']

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
              <div className="field-group">
                <label className="field-label">
                  Sektör <span className="required-star">*</span>
                  <span className="field-hint"> — AI bu sektöre özel içerik üretir</span>
                </label>
                <div className="sector-grid">
                  {sectors.map(s => (
                    <label key={s.id} className={`sector-opt ${form.sector_id === s.id ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="sector"
                        value={s.id}
                        checked={form.sector_id === s.id}
                        onChange={() => setForm({ ...form, sector_id: s.id })}
                      />
                      {s.display_name}
                    </label>
                  ))}
                </div>
              </div>
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
                        rows={5}
                        value={(profil[soru.key] as string) || ''}
                        onChange={e => setProfilField(soru.key, e.target.value)}
                      />
                      {(() => {
                        const len = ((profil[soru.key] as string) || '').length
                        const underMin = soru.minLen && len > 0 && len < soru.minLen
                        const color = underMin ? 'var(--warning-text)' : len > 0 ? 'var(--success-text)' : 'var(--text-quaternary)'
                        return (
                          <span className="char-count" style={{ color }}>
                            {len} / {soru.maxLen}
                            {underMin && ` — en az ${soru.minLen} karakter`}
                          </span>
                        )
                      })()}
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

        {/* ── Adım 3: Kurucu & Hikaye ── */}
        {step === 3 && (
          <Card padding="lg">
            <h2>Kurucu & Marka Hikayesi</h2>
            <p className="desc">
              Bu bilgiler ChatGPT, Perplexity ve Google&apos;ın markanızı bir <strong>gerçek kişiyle</strong> ilişkilendirmesini sağlar.
              E-E-A-T sinyali olarak içeriklerinize ve llms.txt dosyanıza yansıtılır.
            </p>
            <div className="profil-grid">

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">1</span>Kurucu / Marka sahibinin adı soyadı<span className="required-star"> *</span></label>
                <input className="text-input" placeholder="Örn: Ayşe Kaya" value={kurucu.kurucu_adi || ''} onChange={e => setKurucuField('kurucu_adi', e.target.value)} />
              </div>

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">2</span>Unvan / Rol</label>
                <input className="text-input" placeholder="Örn: Kurucu & Baş Tasarımcı, CEO, Girişimci" value={kurucu.unvan || ''} onChange={e => setKurucuField('unvan', e.target.value)} />
              </div>

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">3</span>Markanın kuruluş yılı</label>
                <input className="text-input" placeholder="Örn: 2018" value={kurucu.kurulis_yili || ''} onChange={e => setKurucuField('kurulis_yili', e.target.value)} />
              </div>

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">4</span>Kurucunun kısa biyografisi</label>
                <p className="soru-hint">Hangi geçmişten geliyor, neden bu markayı kurdu? (min 100 / max 1000 karakter)</p>
                <textarea
                  className="textarea-input"
                  rows={4}
                  placeholder="Örn: 15 yıl tekstil sektöründe çalıştıktan sonra 2018'de kendi markasını kurdu. Sürdürülebilir moda konusunda uzman..."
                  maxLength={1000}
                  value={kurucu.biyografi || ''}
                  onChange={e => setKurucuField('biyografi', e.target.value)}
                />
                {(() => {
                  const len = (kurucu.biyografi || '').length
                  const color = len > 0 && len < 100 ? 'var(--warning-text)' : len >= 100 ? 'var(--success-text)' : 'var(--text-quaternary)'
                  return <span className="char-count" style={{ color }}>{len} / 1000{len > 0 && len < 100 ? ' — en az 100 karakter' : ''}</span>
                })()}
              </div>

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">5</span>Markanın ilham kaynağı</label>
                <textarea
                  className="textarea-input"
                  rows={3}
                  placeholder="Örn: Annesinin dikiş makinesiyle başladığı küçük atölye, büyük bedenlere uygun giysi bulmanın zorluğu..."
                  maxLength={500}
                  value={kurucu.ilham || ''}
                  onChange={e => setKurucuField('ilham', e.target.value)}
                />
                <span className="char-count">{(kurucu.ilham || '').length} / 500</span>
              </div>

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">6</span>Ödül / Sertifika / Basın haberi</label>
                <input className="text-input" placeholder="Örn: 2022 Girişimci Ödülü, Vogue Türkiye'de yer aldı" value={kurucu.odul_basin || ''} onChange={e => setKurucuField('odul_basin', e.target.value)} />
              </div>

              <div className="soru-blok">
                <label className="soru-label"><span className="soru-no">7</span>Sosyal medya / Web sitesi</label>
                <input className="text-input" placeholder="Örn: instagram.com/aysekaya, linkedin.com/in/aysekaya" value={kurucu.sosyal_medya || ''} onChange={e => setKurucuField('sosyal_medya', e.target.value)} />
              </div>

            </div>
            <div className="actions">
              <Button variant="ghost" onClick={goBack}>← Geri</Button>
              <Button variant="gradient" onClick={saveStep3} loading={saving}>Kaydet & Tamamla →</Button>
            </div>
          </Card>
        )}

        {/* ── Adım 4: Tamamlandı ── */}
        {step === 4 && (
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

        .fields { display: flex; flex-direction: column; gap: 20px; margin-bottom: 24px; }
        .field-group { display: flex; flex-direction: column; gap: 8px; }
        .field-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }
        .field-hint { color: var(--text-tertiary); font-weight: var(--weight-normal); }
        .sector-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .sector-opt {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          border: 1px solid var(--border-default);
          border-radius: var(--radius-full);
          font-size: var(--text-sm);
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
          background: var(--surface-1);
          color: var(--text-secondary);
          user-select: none;
        }
        .sector-opt:hover { border-color: var(--brand-border); color: var(--text-primary); }
        .sector-opt.selected {
          background: var(--brand-subtle);
          border-color: var(--brand-border);
          color: var(--brand-text);
          font-weight: var(--weight-medium);
        }
        .sector-opt input { display: none; }
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
