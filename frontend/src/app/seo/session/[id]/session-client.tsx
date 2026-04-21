'use client'

import { useState, useMemo, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Badge, Progress, useToast } from '@/components/ui'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AIResult {
  id: string
  stok_kodu: string
  urun_adi: string
  original_seo_baslik?: string | null
  original_seo_aciklama?: string | null
  original_aciklama?: string | null
  ai_urun_adi: string
  ai_seo_baslik: string
  ai_seo_aciklama: string
  ai_onyazi: string
  ai_aciklama?: string | null
  ai_anahtar_kelime?: string | null
  ai_seo_anahtar_kelime?: string | null
  ai_geo_sss?: string | null
  ai_schema_jsonld?: string | null
  ai_breadcrumb_kat?: string | null
  ai_adwords_aciklama?: string | null
  ai_adwords_kategori?: string | null
  ai_adwords_tip?: string | null
  ai_ozelalan_1?: string | null
  ai_ozelalan_2?: string | null
  ai_ozelalan_3?: string | null
  ai_ozelalan_4?: string | null
  ai_ozelalan_5?: string | null
  ai_claim_map?: string | null
  ai_information_gain?: number | null
  ai_uyarilar?: string | null
  image_url?: string | null
  status: string
}

interface Session {
  id: string
  job_name: string
  status: string
  total_products: number
  processed_products: number
  created_at: string
  completed_at?: string | null
  organizations?: {
    id: string
    company_name: string
    ws_kodu: string | null
    domain_url: string | null
  } | null
}

interface SessionClientProps {
  session: Session
  initialResults: AIResult[]
}

type Decision = 'pending' | 'approved' | 'rejected'

export default function SessionClient({ session, initialResults }: SessionClientProps) {
  const router = useRouter()
  const toast = useToast()
  const supabase = createClient()

  const [results, setResults] = useState(initialResults)
  const [currentIdx, setCurrentIdx] = useState(0)
  const [decisions, setDecisions] = useState<Record<string, Decision>>({})
  const [sending, setSending] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [localStatus, setLocalStatus] = useState(session.status)

  const current = results[currentIdx]
  const isProcessing = localStatus === 'processing' || localStatus === 'pending'
  const isCancelled = localStatus === 'cancelled'

  const cancelAnalysis = async () => {
    if (cancelling) return
    if (!confirm('Devam eden analizi durdurmak istediğine emin misin? İşlenmiş ürünler korunur, bekleyenler iptal edilir.')) return
    setCancelling(true)
    try {
      await fetch(`${API}/api/analyze/cancel/${session.id}`, { method: 'POST' })
      await supabase
        .from('ai_sessions')
        .update({ status: 'cancelled', completed_at: new Date().toISOString() })
        .eq('id', session.id)
      setLocalStatus('cancelled')
      toast.show('Analiz durduruldu', 'info')
      router.refresh()
    } catch {
      toast.show('Durdurma başarısız', 'error')
    } finally {
      setCancelling(false)
    }
  }

  const decisionStats = useMemo(() => {
    let approved = 0, rejected = 0, pending = 0
    for (const r of results) {
      const d = decisions[r.id] || 'pending'
      if (d === 'approved') approved++
      else if (d === 'rejected') rejected++
      else pending++
    }
    return { approved, rejected, pending, total: results.length }
  }, [results, decisions])

  // Poll for updates while processing
  useEffect(() => {
    if (!isProcessing) return
    const poll = async () => {
      try {
        const res = await fetch(`${API}/api/analyze/status/${session.id}`)
        if (!res.ok) return
        const data = await res.json()
        if (data.status === 'completed' || data.status === 'cancelled' || data.status === 'error') {
          const { data: fresh } = await supabase.from('ai_results').select('*').eq('session_id', session.id)
          if (fresh) setResults(fresh)
          setLocalStatus(data.status === 'error' ? 'failed' : data.status)
          router.refresh()
        }
      } catch { /* backend down */ }
    }
    const t = setInterval(poll, 3000)
    return () => clearInterval(t)
  }, [isProcessing, session.id, supabase, router])

  const setDecision = (id: string, d: Decision) => {
    setDecisions(prev => ({ ...prev, [id]: d }))
    if (d === 'approved' && currentIdx < results.length - 1) {
      setTimeout(() => setCurrentIdx(currentIdx + 1), 200)
    }
  }

  const approveAll = () => {
    const next: Record<string, Decision> = {}
    for (const r of results) next[r.id] = 'approved'
    setDecisions(next)
    toast.show(`${results.length} ürün onaylandı`, 'success')
  }

  const downloadFile = (filename: string, blob: Blob) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const safeFileName = (s: string) =>
    s.replace(/[^a-zA-Z0-9-_ğüşıöçĞÜŞİÖÇ]/g, '_').slice(0, 50)

  const exportJSON = () => {
    if (results.length === 0) return toast.show('Sonuç yok', 'warning')
    const payload = {
      session: {
        id: session.id,
        job_name: session.job_name,
        status: localStatus,
        total_products: session.total_products,
        processed_products: session.processed_products,
        created_at: session.created_at,
        completed_at: session.completed_at,
        organization: session.organizations?.company_name,
      },
      results: results.map(r => ({
        stok_kodu: r.stok_kodu,
        original: {
          urun_adi: r.urun_adi,
          seo_baslik: r.original_seo_baslik,
          seo_aciklama: r.original_seo_aciklama,
          aciklama: r.original_aciklama,
        },
        ai: {
          urun_adi: r.ai_urun_adi,
          seo_baslik: r.ai_seo_baslik,
          seo_aciklama: r.ai_seo_aciklama,
          onyazi: r.ai_onyazi,
          aciklama: r.ai_aciklama,
          anahtar_kelime: r.ai_anahtar_kelime,
          seo_anahtar_kelime: r.ai_seo_anahtar_kelime,
          geo_sss: r.ai_geo_sss,
          schema_jsonld: r.ai_schema_jsonld,
          breadcrumb_kat: r.ai_breadcrumb_kat,
          adwords_aciklama: r.ai_adwords_aciklama,
          adwords_kategori: r.ai_adwords_kategori,
          adwords_tip: r.ai_adwords_tip,
          ozelalan_1: r.ai_ozelalan_1,
          ozelalan_2: r.ai_ozelalan_2,
          ozelalan_3: r.ai_ozelalan_3,
          ozelalan_4: r.ai_ozelalan_4,
          ozelalan_5: r.ai_ozelalan_5,
          claim_map: r.ai_claim_map,
          information_gain_skoru: r.ai_information_gain,
          uyarilar: r.ai_uyarilar,
        },
        decision: decisions[r.id] || 'pending',
        image_url: r.image_url,
        status: r.status,
      })),
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    downloadFile(`pixra_${safeFileName(session.job_name)}_${session.id.slice(0, 8)}.json`, blob)
    toast.show('JSON indirildi', 'success')
  }

  const exportExcel = async () => {
    if (results.length === 0) return toast.show('Sonuç yok', 'warning')
    try {
      const XLSX = await import('xlsx')
      const rows = results.map(r => ({
        'Stok Kodu': r.stok_kodu,
        'Karar': decisions[r.id] === 'approved' ? 'Onaylandı'
                : decisions[r.id] === 'rejected' ? 'Reddedildi' : 'Bekliyor',
        'Orijinal Ürün Adı': r.urun_adi || '',
        'AI Ürün Adı': r.ai_urun_adi || '',
        'AI SEO Başlık': r.ai_seo_baslik || '',
        'AI SEO Açıklama': r.ai_seo_aciklama || '',
        'AI Pazarlama Önyazısı': r.ai_onyazi || '',
        'AI Açıklama (HTML)': r.ai_aciklama || '',
        'AI Anahtar Kelime (mağaza içi)': r.ai_anahtar_kelime || '',
        'AI SEO Anahtar Kelime': r.ai_seo_anahtar_kelime || '',
        'AI GEO SSS': r.ai_geo_sss || '',
        'AI Adwords Açıklama': r.ai_adwords_aciklama || '',
        'AI Adwords Kategori': r.ai_adwords_kategori || '',
        'AI Adwords Tip': r.ai_adwords_tip || '',
        'AI Breadcrumb': r.ai_breadcrumb_kat || '',
        'AI ÖzelAlan 1': r.ai_ozelalan_1 || '',
        'AI ÖzelAlan 2': r.ai_ozelalan_2 || '',
        'AI ÖzelAlan 3': r.ai_ozelalan_3 || '',
        'AI ÖzelAlan 4': r.ai_ozelalan_4 || '',
        'AI ÖzelAlan 5': r.ai_ozelalan_5 || '',
        'AI Schema JSON-LD': r.ai_schema_jsonld || '',
        'AI Claim Map': r.ai_claim_map || '',
        'AI Information Gain': r.ai_information_gain ?? '',
        'AI Uyarılar': r.ai_uyarilar || '',
        'Orijinal SEO Başlık': r.original_seo_baslik || '',
        'Orijinal SEO Açıklama': r.original_seo_aciklama || '',
        'Orijinal Açıklama': r.original_aciklama || '',
        'Görsel URL': r.image_url || '',
        'Durum': r.status,
      }))
      const ws = XLSX.utils.json_to_sheet(rows)
      ws['!cols'] = [
        { wch: 14 }, { wch: 12 }, { wch: 30 }, { wch: 30 },
        { wch: 35 }, { wch: 50 }, { wch: 60 }, { wch: 60 },
        { wch: 30 }, { wch: 30 }, { wch: 60 }, { wch: 50 },
        { wch: 35 }, { wch: 30 }, { wch: 20 }, { wch: 20 },
        { wch: 20 }, { wch: 20 }, { wch: 20 }, { wch: 20 },
        { wch: 50 }, { wch: 50 }, { wch: 12 }, { wch: 30 },
        { wch: 30 }, { wch: 50 }, { wch: 50 }, { wch: 40 }, { wch: 12 },
      ]
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, 'Analiz')
      const buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
      const blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      downloadFile(`pixra_${safeFileName(session.job_name)}_${session.id.slice(0, 8)}.xlsx`, blob)
      toast.show('Excel indirildi', 'success')
    } catch (e) {
      toast.show('Excel oluşturulamadı: ' + (e instanceof Error ? e.message : ''), 'error')
    }
  }

  const sendApprovedToTicimax = async () => {
    const approvedResults = results.filter(r => decisions[r.id] === 'approved')
    if (approvedResults.length === 0) return toast.show('Önce ürünleri onayla', 'warning')

    const org = session.organizations
    if (!org?.ws_kodu || !org?.domain_url) {
      return toast.show('Ticimax bilgileri eksik — Ayarlar\'dan ws_kodu ve domain_url gir', 'error')
    }

    const products = approvedResults.map(r => ({
      stok_kodu: r.stok_kodu,
      urun_adi: r.ai_urun_adi || '',
      aciklama: r.ai_aciklama || r.ai_onyazi || '',
      seo_baslik: r.ai_seo_baslik || '',
      seo_aciklama: r.ai_seo_aciklama || '',
      seo_anahtarkelime: r.ai_seo_anahtar_kelime || r.ai_anahtar_kelime || '',
      onyazi: r.ai_onyazi || '',
      // Pazarlama sekmesi (Adwords Ürün Feed alanları)
      adwords_aciklama: r.ai_adwords_aciklama || '',
      adwords_kategori: r.ai_adwords_kategori || '',
      adwords_tip: r.ai_adwords_tip || '',
    }))

    setSending(true)
    try {
      const res = await fetch(`${API}/api/ticimax/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_url: org.domain_url,
          ws_kodu: org.ws_kodu,
          products,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data.detail || 'send failed')
      }
      const successCount = Array.isArray(data.results)
        ? data.results.filter((x: { status: string }) => x.status === 'success').length
        : products.length
      const errorCount = products.length - successCount
      if (errorCount > 0) {
        toast.show(`${successCount} başarılı, ${errorCount} hata — detay için konsol`, 'warning')
        console.warn('Ticimax send partial errors:', data.results)
      } else {
        toast.show(`${successCount} ürün Ticimax'e gönderildi`, 'success')
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Bilinmeyen hata'
      toast.show(`Ticimax'e gönderim başarısız: ${msg}`, 'error')
    } finally {
      setSending(false)
    }
  }

  const percentComplete = session.total_products > 0
    ? (session.processed_products / session.total_products) * 100
    : 0

  // Empty state while processing
  if (isProcessing && results.length === 0) {
    return (
      <>
        <HeaderRow session={session} status={localStatus} onBack={() => router.push('/seo')} />
        <Card variant="magic" padding="lg">
          <div className="processing">
            <div className="processing-icon">
              <div className="spinner-lg" />
            </div>
            <h2>AI Analizi Devam Ediyor</h2>
            <p>Ürünleriniz yapay zekâ ile analiz ediliyor. Bu işlem birkaç dakika sürebilir.</p>
            <div style={{ maxWidth: 420, width: '100%' }}>
              <Progress value={percentComplete} showPercent label={`${session.processed_products} / ${session.total_products} ürün`} />
            </div>
            <Button variant="danger" size="md" loading={cancelling} onClick={cancelAnalysis}>
              ⏹ Analizi Durdur
            </Button>
          </div>
        </Card>
        <style jsx>{processingStyles}</style>
      </>
    )
  }

  if (isCancelled && results.length === 0) {
    return (
      <>
        <HeaderRow session={session} status={localStatus} onBack={() => router.push('/seo')} />
        <Card padding="lg">
          <p style={{ textAlign: 'center', color: 'var(--text-tertiary)' }}>
            Bu analiz durduruldu. Hiçbir ürün işlenmeden iptal edildi.
          </p>
        </Card>
      </>
    )
  }

  if (!current) {
    return (
      <>
        <HeaderRow session={session} status={localStatus} onBack={() => router.push('/seo')} />
        <Card padding="lg">
          <p style={{ textAlign: 'center', color: 'var(--text-tertiary)' }}>Bu oturumda henüz sonuç yok.</p>
        </Card>
      </>
    )
  }

  const currentDecision = decisions[current.id] || 'pending'

  return (
    <>
      <HeaderRow session={session} status={localStatus} onBack={() => router.push('/seo')} />

      {/* ── Summary Bar ── */}
      <Card padding="md" variant="elevated" className="summary-bar">
        <div className="summary">
          <div className="summary-metric">
            <span className="caption">İşlenen</span>
            <strong>{session.processed_products}/{session.total_products}</strong>
          </div>
          <div className="summary-divider" />
          <div className="summary-metric">
            <span className="caption">Onaylanan</span>
            <strong style={{ color: 'var(--success-text)' }}>{decisionStats.approved}</strong>
          </div>
          <div className="summary-metric">
            <span className="caption">Reddedilen</span>
            <strong style={{ color: 'var(--error-text)' }}>{decisionStats.rejected}</strong>
          </div>
          <div className="summary-metric">
            <span className="caption">Bekleyen</span>
            <strong>{decisionStats.pending}</strong>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {isProcessing && (
              <Button variant="danger" size="sm" loading={cancelling} onClick={cancelAnalysis}>
                ⏹ Durdur
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={exportExcel} title="Excel olarak indir">
              ⬇ Excel
            </Button>
            <Button variant="ghost" size="sm" onClick={exportJSON} title="JSON olarak indir">
              ⬇ JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={approveAll}>
              Hepsini Onayla
            </Button>
            <Button
              variant="gradient"
              size="sm"
              loading={sending}
              onClick={sendApprovedToTicimax}
              disabled={decisionStats.approved === 0}
            >
              Ticimax'e Gönder ({decisionStats.approved})
            </Button>
          </div>
        </div>
      </Card>

      {/* ── Navigation ── */}
      <div className="nav-row">
        <div className="nav-counter">
          Ürün <strong>{currentIdx + 1}</strong> / {results.length}
        </div>
        <div className="nav-buttons">
          <Button variant="ghost" size="sm" onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))} disabled={currentIdx === 0}>
            ← Önceki
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setCurrentIdx(Math.min(results.length - 1, currentIdx + 1))} disabled={currentIdx === results.length - 1}>
            Sonraki →
          </Button>
        </div>
      </div>

      {/* ── Before/After Hero ── */}
      <div className="compare-grid">
        {/* Before */}
        <Card padding="lg" className="compare-col before">
          <div className="compare-label">
            <Badge tone="neutral" soft>ÖNCE</Badge>
            <span>Mevcut içerik</span>
          </div>
          {current.image_url && (
            <div className="product-thumb">
              <img src={current.image_url} alt={current.urun_adi} />
            </div>
          )}
          <Field label="Ürün Adı" value={current.urun_adi} tone="muted" />
          <Field label="SEO Başlık" value={current.original_seo_baslik || '(boş)'} tone="muted" />
          <Field label="Açıklama" value={current.original_aciklama || '(boş)'} tone="muted" multiline />
          <Field label="SEO Açıklama" value={current.original_seo_aciklama || '(boş)'} tone="muted" multiline />
        </Card>

        {/* After */}
        <Card variant="magic" padding="lg" className="compare-col after">
          <div className="compare-label magic">
            <Badge tone="brand" soft dot>AI İLE</Badge>
            <span className="text-gradient" style={{ fontWeight: 600 }}>Optimize edilmiş içerik</span>
          </div>
          {current.image_url && (
            <div className="product-thumb">
              <img src={current.image_url} alt={current.ai_urun_adi} />
            </div>
          )}
          <Field label="Ürün Adı" value={current.ai_urun_adi} tone="primary" />
          <Field
            label="SEO Başlık"
            value={current.ai_seo_baslik}
            tone="primary"
            meta={<CharCount value={current.ai_seo_baslik?.length || 0} max={60} />}
          />
          <Field label="Pazarlama Önyazısı" value={current.ai_onyazi} tone="primary" multiline />
          {current.ai_aciklama && (
            <Field label="Açıklama (HTML)" value={current.ai_aciklama} tone="primary" multiline />
          )}
          <Field
            label="SEO Açıklama"
            value={current.ai_seo_aciklama}
            tone="primary"
            multiline
            meta={<CharCount value={current.ai_seo_aciklama?.length || 0} max={155} />}
          />
          {current.ai_seo_anahtar_kelime && (
            <Field label="SEO Anahtar Kelime" value={current.ai_seo_anahtar_kelime} tone="primary" />
          )}
          {current.ai_anahtar_kelime && (
            <Field label="Mağaza İçi Anahtar Kelime" value={current.ai_anahtar_kelime} tone="primary" />
          )}
          {(current.ai_ozelalan_1 || current.ai_ozelalan_2 || current.ai_ozelalan_3) && (
            <Field
              label="Özel Alanlar (Ticimax filtre)"
              value={[current.ai_ozelalan_1, current.ai_ozelalan_2, current.ai_ozelalan_3, current.ai_ozelalan_4, current.ai_ozelalan_5].filter(Boolean).join(' • ')}
              tone="primary"
            />
          )}
          {typeof current.ai_information_gain === 'number' && (
            <Field label="Information Gain Skoru" value={`${current.ai_information_gain} / 10`} tone="primary" />
          )}
        </Card>
      </div>

      {/* ── Decision Bar ── */}
      <div className="decision-bar">
        <Button
          variant={currentDecision === 'rejected' ? 'danger' : 'ghost'}
          size="lg"
          onClick={() => setDecision(current.id, 'rejected')}
        >
          ✕ Reddet
        </Button>
        <Button variant="ghost" size="lg" onClick={() => toast.show('Yeniden analiz talep edildi', 'info')}>
          ↻ AI'dan Yeniden İste
        </Button>
        <Button
          variant={currentDecision === 'approved' ? 'primary' : 'gradient'}
          size="lg"
          onClick={() => setDecision(current.id, 'approved')}
        >
          {currentDecision === 'approved' ? '✓ Onaylandı' : '✓ Onayla ve Sonraki'}
        </Button>
      </div>

      <style jsx>{`
        :global(.summary-bar) { margin-bottom: 20px; }
        .summary {
          display: flex;
          align-items: center;
          gap: 20px;
          flex-wrap: wrap;
        }
        .summary-metric {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .summary-metric strong {
          font-size: var(--text-lg);
          font-variant-numeric: tabular-nums;
          line-height: 1;
        }
        .summary-divider {
          width: 1px;
          height: 28px;
          background: var(--border-subtle);
        }

        .nav-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .nav-counter {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
        }
        .nav-counter strong { color: var(--text-primary); font-weight: var(--weight-bold); }
        .nav-buttons {
          display: flex;
          gap: 6px;
        }

        .compare-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-bottom: 20px;
        }
        .compare-label {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--border-subtle);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .compare-label.magic {
          border-bottom-color: rgba(168, 85, 247, 0.2);
        }

        .product-thumb {
          width: 100%;
          aspect-ratio: 16/10;
          border-radius: var(--radius-md);
          overflow: hidden;
          margin-bottom: 16px;
          background: var(--surface-3);
        }
        .product-thumb img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .decision-bar {
          position: sticky;
          bottom: 16px;
          display: flex;
          justify-content: center;
          gap: 10px;
          padding: 14px;
          background: var(--surface-2);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-lg);
          backdrop-filter: blur(12px);
        }

        @media (max-width: 900px) {
          .compare-grid { grid-template-columns: 1fr; }
          .decision-bar { flex-direction: column; }
        }
      `}</style>
    </>
  )
}

function HeaderRow({ session, status, onBack }: { session: Session; status: string; onBack: () => void }) {
  return (
    <div className="header-row">
      <Button variant="ghost" size="sm" onClick={onBack}>← Tümü</Button>
      <div style={{ flex: 1 }}>
        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 600, margin: 0 }}>{session.job_name}</h1>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
          {session.organizations?.company_name} • {new Date(session.created_at).toLocaleString('tr-TR')}
        </span>
      </div>
      <Badge
        tone={status === 'completed' ? 'success' : status === 'processing' ? 'info' : status === 'cancelled' ? 'warning' : status === 'failed' ? 'danger' : 'neutral'}
        dot
      >
        {status === 'completed' && 'Tamamlandı'}
        {status === 'processing' && 'İşleniyor'}
        {status === 'pending' && 'Bekliyor'}
        {status === 'cancelled' && 'Durduruldu'}
        {status === 'failed' && 'Hata'}
      </Badge>
      <style jsx>{`
        .header-row {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-bottom: 20px;
        }
      `}</style>
    </div>
  )
}

function Field({
  label,
  value,
  tone = 'primary',
  multiline,
  meta,
}: {
  label: string
  value: string
  tone?: 'primary' | 'muted'
  multiline?: boolean
  meta?: React.ReactNode
}) {
  return (
    <div className={`field ${tone} ${multiline ? 'multi' : ''}`}>
      <div className="field-label">
        <span>{label}</span>
        {meta}
      </div>
      <div className="field-value">{value}</div>
      <style jsx>{`
        .field {
          padding: 10px 0;
          border-bottom: 1px solid var(--border-subtle);
        }
        .field:last-child { border-bottom: none; }
        .field-label {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: var(--tracking-caps);
          font-weight: var(--weight-semibold);
          margin-bottom: 6px;
        }
        .field-value {
          font-size: var(--text-base);
          line-height: 1.5;
        }
        .multi .field-value {
          white-space: pre-wrap;
        }
        .primary .field-value { color: var(--text-primary); font-weight: var(--weight-medium); }
        .muted .field-value { color: var(--text-tertiary); }
      `}</style>
    </div>
  )
}

function CharCount({ value, max }: { value: number; max: number }) {
  const ok = value > 0 && value <= max
  const empty = value === 0
  return (
    <Badge tone={empty ? 'neutral' : ok ? 'success' : 'warning'} soft>
      {value}/{max}
    </Badge>
  )
}

const processingStyles = `
  .processing {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 60px 20px;
    text-align: center;
  }
  .processing-icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: var(--brand-subtle);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
  }
  .spinner-lg {
    width: 28px;
    height: 28px;
    border: 3px solid var(--brand-subtle);
    border-top-color: var(--brand-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  .processing h2 { margin: 0; font-size: var(--text-xl); }
  .processing p { color: var(--text-tertiary); max-width: 420px; }
`
