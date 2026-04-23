'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Badge, Input, EmptyState, useToast } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Firm {
  id: string
  company_name: string
  domain_url: string | null
  ws_kodu: string
  gemini_api_key: string | null
}

interface Product {
  id: number
  stok_kodu: string
  display_stok: string
  urun_adi: string
  resim_url: string
}

type Phase = 'fetching' | 'ready' | 'starting' | 'error'

export default function NewAnalysisClient({ firm, userId, credits, readOnly }: {
  firm: Firm
  userId: string
  credits: number
  readOnly: boolean
}) {
  const router = useRouter()
  const toast = useToast()
  const supabase = createClient()

  const [phase, setPhase] = useState<Phase>('fetching')
  const [products, setProducts] = useState<Product[]>([])
  const [fetchError, setFetchError] = useState('')
  const [fromCache, setFromCache] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [search, setSearch] = useState('')
  const [jobName, setJobName] = useState('')

  const fetchProducts = async (forceRefresh = false) => {
    setPhase('fetching')
    setFetchError('')
    try {
      const res = await fetch(`${API}/api/products/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_url: firm.domain_url || '',
          ws_kodu: firm.ws_kodu,
          organization_id: firm.id,
          force_refresh: forceRefresh,
        }),
      })
      const data = await res.json()
      if (data.status === 'success') {
        setProducts(data.products || [])
        setFromCache(!!data.from_cache)
        setPhase('ready')
      } else {
        setFetchError(data.error || 'Ürünler çekilemedi')
        setPhase('error')
      }
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : 'Backend bağlantısı başarısız')
      setPhase('error')
    }
  }

  useEffect(() => { fetchProducts() }, [firm.domain_url, firm.ws_kodu])

  const filtered = useMemo(() => {
    if (!search.trim()) return products
    const q = search.toLowerCase()
    return products.filter(p =>
      p.urun_adi.toLowerCase().includes(q) ||
      p.display_stok.toLowerCase().includes(q)
    )
  }, [products, search])

  const allFilteredSelected = filtered.length > 0 && filtered.every(p => selected.has(p.stok_kodu))
  const selectedCount = selected.size
  const insufficientCredit = selectedCount > credits
  const canStart = !readOnly && selectedCount > 0 && !insufficientCredit && jobName.trim().length > 0

  const toggleOne = (stok: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(stok)) next.delete(stok)
      else next.add(stok)
      return next
    })
  }

  const toggleAllFiltered = () => {
    setSelected(prev => {
      const next = new Set(prev)
      if (allFilteredSelected) {
        filtered.forEach(p => next.delete(p.stok_kodu))
      } else {
        filtered.forEach(p => next.add(p.stok_kodu))
      }
      return next
    })
  }

  const selectAllInCatalog = () => {
    setSelected(new Set(products.map(p => p.stok_kodu)))
  }

  const clearSelection = () => setSelected(new Set())

  const startAnalysis = async () => {
    if (!canStart) return
    if (readOnly) return toast.show('Impersonate modunda değiştirilemez', 'warning')
    setPhase('starting')

    const { data: session, error } = await supabase
      .from('ai_sessions')
      .insert({
        organization_id: firm.id,
        user_id: userId,
        job_name: jobName.trim(),
        status: 'pending',
        total_products: selectedCount,
        processed_products: 0,
      })
      .select()
      .single()

    if (error || !session) {
      toast.show('Oturum oluşturulamadı', 'error')
      setPhase('ready')
      return
    }

    try {
      await fetch(`${API}/api/analyze/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ws_kodu: firm.ws_kodu,
          api_key: firm.gemini_api_key || '',
          selected_products: Array.from(selected),
          firma_kodu: firm.id,
          domain_url: firm.domain_url || '',
          brand_name: firm.company_name,
          session_id: session.id,
          organization_id: firm.id,
        }),
      })
      toast.show('Analiz başlatıldı', 'success')
      router.push(`/seo/session/${session.id}`)
    } catch {
      toast.show('Backend bağlantısı başarısız', 'error')
      setPhase('ready')
    }
  }

  return (
    <>
      <PageHeader
        title="Yeni Analiz"
        description="Mağazandan ürünleri çek, istediklerini seç, AI içerik üretsin"
        breadcrumb={
          <span>
            <a href="/seo" style={{ color: 'var(--text-tertiary)', textDecoration: 'none' }}>SEO</a> / Yeni Analiz
          </span>
        }
      />

      {phase === 'fetching' && (
        <Card padding="lg" variant="flat">
          <div className="loading-state">
            <div className="spinner" />
            <h3>Ürünler çekiliyor…</h3>
            <p>Ticimax'ten mağaza kataloğun indiriliyor. Mağaza boyutuna göre 10-60 saniye sürebilir.</p>
          </div>
        </Card>
      )}

      {phase === 'error' && (
        <Card padding="lg" variant="flat">
          <EmptyState
            title="Ürünler çekilemedi"
            description={fetchError}
            action={
              <div style={{ display: 'flex', gap: 8 }}>
                <Button variant="secondary" onClick={() => router.push('/settings')}>Ayarları Kontrol Et</Button>
                <Button variant="primary" onClick={() => window.location.reload()}>Tekrar Dene</Button>
              </div>
            }
          />
        </Card>
      )}

      {(phase === 'ready' || phase === 'starting') && (
        <>
          <div className="summary-bar">
            <div className="summary-left">
              <div className="sum-num">{products.length.toLocaleString('tr-TR')}</div>
              <div className="sum-lbl">
                {fromCache ? 'ürün (önbellekten)' : 'ürün çekildi'}
              </div>
              <button
                className="refresh-btn"
                onClick={() => fetchProducts(true)}
                title="Ticimax'ten yeniden çek"
              >
                ↻ Yenile
              </button>
            </div>
            <div className="summary-mid">
              <Input
                placeholder="Ürün adı veya SKU ara…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <div className="summary-right">
              <Badge tone={insufficientCredit ? 'danger' : selectedCount > 0 ? 'brand' : 'neutral'} soft>
                {selectedCount} seçildi · {credits.toLocaleString('tr-TR')} kredi
              </Badge>
            </div>
          </div>

          <div className="bulk-bar">
            <label className="bulk-check">
              <input
                type="checkbox"
                checked={allFilteredSelected}
                onChange={toggleAllFiltered}
              />
              <span>
                {search.trim()
                  ? `Filtrelenenleri seç (${filtered.length})`
                  : `Görünenleri seç (${filtered.length})`}
              </span>
            </label>
            <div className="bulk-actions">
              <button className="linkish" onClick={selectAllInCatalog} disabled={readOnly}>
                Tüm katalogu seç ({products.length})
              </button>
              <span className="sep">·</span>
              <button className="linkish" onClick={clearSelection} disabled={selectedCount === 0}>
                Seçimi temizle
              </button>
            </div>
          </div>

          {filtered.length === 0 ? (
            <Card padding="lg" variant="flat">
              <EmptyState title="Ürün bulunamadı" description={search ? 'Arama kriterine uyan ürün yok.' : 'Mağazanda ürün görünmüyor.'} />
            </Card>
          ) : (
            <div className="product-grid">
              {filtered.map(p => {
                const isSel = selected.has(p.stok_kodu)
                return (
                  <div
                    key={p.stok_kodu}
                    className={`product-tile ${isSel ? 'selected' : ''}`}
                    onClick={() => toggleOne(p.stok_kodu)}
                  >
                    <div className="tile-img">
                      {p.resim_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={p.resim_url} alt={p.urun_adi} loading="lazy" />
                      ) : (
                        <div className="no-img">🖼️</div>
                      )}
                      <div className="tile-check">
                        <input type="checkbox" checked={isSel} readOnly />
                      </div>
                    </div>
                    <div className="tile-body">
                      <div className="tile-name" title={p.urun_adi}>{p.urun_adi}</div>
                      <div className="tile-sku">{p.display_stok}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          <div className="action-bar">
            <div className="ab-left">
              <Input
                label="İş Adı"
                placeholder="Örn: Nisan 2026 — Kadın Çanta"
                value={jobName}
                onChange={e => setJobName(e.target.value)}
                required
              />
            </div>
            <div className="ab-right">
              <div className="cost-line">
                <span className="cost-num">{selectedCount}</span>
                <span className="cost-unit">kredi kullanılacak</span>
              </div>
              {insufficientCredit && (
                <div className="cost-warn">⚠ Yetersiz kredi · <a href="/credits">kredi al</a></div>
              )}
              <Button
                variant="gradient"
                size="lg"
                onClick={startAnalysis}
                disabled={!canStart}
                loading={phase === 'starting'}
              >
                Analizi Başlat →
              </Button>
            </div>
          </div>
        </>
      )}

      <style jsx>{`
        .loading-state {
          text-align: center;
          padding: 40px 20px;
        }
        .loading-state h3 {
          margin: 16px 0 8px;
          font-size: var(--text-lg);
        }
        .loading-state p {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          margin: 0;
        }
        .spinner {
          width: 36px;
          height: 36px;
          border: 3px solid var(--border-default);
          border-top-color: var(--brand-primary);
          border-radius: 50%;
          margin: 0 auto;
          animation: spin 0.8s linear infinite;
        }

        .summary-bar {
          display: grid;
          grid-template-columns: auto 1fr auto;
          gap: 16px;
          align-items: center;
          padding: 14px 16px;
          background: var(--surface-1);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          margin-bottom: 12px;
        }
        .summary-left {
          display: flex;
          flex-direction: column;
          line-height: 1.1;
        }
        .sum-num {
          font-size: var(--text-xl);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }
        .sum-lbl {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .refresh-btn {
          margin-top: 4px;
          background: none;
          border: none;
          color: var(--brand-text);
          font-size: var(--text-xs);
          cursor: pointer;
          padding: 0;
          font-weight: var(--weight-medium);
        }
        .refresh-btn:hover { text-decoration: underline; }

        .bulk-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 4px;
          margin-bottom: 8px;
          font-size: var(--text-sm);
        }
        .bulk-check {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--text-secondary);
          cursor: pointer;
        }
        .bulk-check input[type='checkbox'] {
          width: 16px;
          height: 16px;
          accent-color: var(--brand-primary);
          cursor: pointer;
        }
        .bulk-actions {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: var(--text-xs);
        }
        .linkish {
          background: none;
          border: none;
          color: var(--brand-text);
          cursor: pointer;
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
          padding: 0;
        }
        .linkish:hover { text-decoration: underline; }
        .linkish:disabled { color: var(--text-muted); cursor: not-allowed; text-decoration: none; }
        .sep { color: var(--text-muted); }

        .product-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 12px;
          margin-bottom: 100px;
        }
        .product-tile {
          background: var(--surface-1);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          overflow: hidden;
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
          user-select: none;
        }
        .product-tile:hover {
          border-color: var(--border-default);
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
        }
        .product-tile.selected {
          border-color: var(--brand-primary);
          box-shadow: 0 0 0 2px var(--brand-subtle);
        }
        .tile-img {
          position: relative;
          aspect-ratio: 1;
          background: var(--surface-2);
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }
        .tile-img img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .no-img {
          font-size: 2rem;
          opacity: 0.3;
        }
        .tile-check {
          position: absolute;
          top: 8px;
          left: 8px;
          background: rgba(0,0,0,0.6);
          border-radius: var(--radius-sm);
          padding: 2px 4px;
          backdrop-filter: blur(4px);
        }
        .tile-check input {
          width: 16px;
          height: 16px;
          accent-color: var(--brand-primary);
          display: block;
          pointer-events: none;
        }
        .tile-body {
          padding: 10px 12px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .tile-name {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
          line-height: 1.35;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .tile-sku {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          font-family: var(--font-mono, monospace);
        }

        .action-bar {
          position: fixed;
          bottom: 0;
          left: var(--sidebar-w);
          right: 0;
          z-index: var(--z-sidebar);
          background: var(--surface-1);
          border-top: 1px solid var(--border-subtle);
          padding: 14px 36px;
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 20px;
          align-items: end;
          box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.25);
        }
        .ab-left { max-width: 420px; }
        .ab-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 6px;
        }
        .cost-line {
          display: flex;
          align-items: baseline;
          gap: 6px;
        }
        .cost-num {
          font-size: var(--text-xl);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }
        .cost-unit {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .cost-warn {
          font-size: var(--text-xs);
          color: var(--error-text);
        }
        .cost-warn a { color: var(--brand-text); }

        @media (max-width: 900px) {
          .summary-bar { grid-template-columns: 1fr; }
          .action-bar { left: 0; padding: 12px 16px; grid-template-columns: 1fr; }
        }
      `}</style>
    </>
  )
}
