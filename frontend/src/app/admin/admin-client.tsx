'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, Badge, Button, EmptyState } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'
import { createClient } from '@/lib/supabase/client'
import { adminDeleteSession } from './actions'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface GeminiKey {
  id: string
  label: string
  api_key_masked: string
  is_active: boolean
  created_at: string
}

interface Kpis { users: number; firms: number; sessions: number; totalCredits: number }

interface Customer {
  id: string
  email: string | null
  full_name: string | null
  created_at: string
  last_sign_in_at: string | null
  credits: number
  session_count: number
  org: {
    id: string
    company_name: string
    domain_url: string | null
    ws_kodu: string | null
    firma_profil?: Record<string, unknown> | null
  } | null
}

interface SessionRow {
  id: string
  job_name: string
  status: string
  total_products: number
  processed_products: number
  created_at: string
  completed_at: string | null
  error_message: string | null
  organizations: { company_name: string } | { company_name: string }[] | null
}

function fmtDuration(created: string, completed: string | null): string {
  if (!completed) return '—'
  const secs = Math.round((new Date(completed).getTime() - new Date(created).getTime()) / 1000)
  if (secs < 0) return '—'
  if (secs < 60) return `${secs}sn`
  return `${Math.floor(secs / 60)}dk ${secs % 60}sn`
}

function avgPerProduct(created: string, completed: string | null, count: number): string {
  if (!completed || count === 0) return ''
  const secs = Math.round((new Date(completed).getTime() - new Date(created).getTime()) / 1000)
  const avg = Math.round(secs / count)
  return `~${avg}sn/ürün`
}

function firmName(s: SessionRow): string {
  const o = s.organizations
  if (!o) return '—'
  if (Array.isArray(o)) return o[0]?.company_name || '—'
  return o.company_name || '—'
}

function timeAgo(iso: string | null): string {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}dk önce`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}sa önce`
  return new Date(iso).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })
}

export default function AdminClient({ kpis, customers, recentSessions: initialSessions }: {
  kpis: Kpis
  customers: Customer[]
  recentSessions: SessionRow[]
}) {
  const router = useRouter()
  const [sessions, setSessions] = useState(initialSessions)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Gemini key pool state
  const [geminiKeys, setGeminiKeys] = useState<GeminiKey[]>([])
  const [poolSize, setPoolSize] = useState(0)
  const [newKeyLabel, setNewKeyLabel] = useState('')
  const [newKeyValue, setNewKeyValue] = useState('')
  const [keyLoading, setKeyLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/api/admin/gemini-keys`)
      .then(r => r.json())
      .then(d => { setGeminiKeys(d.keys || []); setPoolSize(d.pool_size || 0) })
      .catch(() => {})
  }, [])

  const addKey = async () => {
    if (!newKeyLabel.trim() || !newKeyValue.trim()) return
    setKeyLoading(true)
    try {
      await fetch(`${API}/api/admin/gemini-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: newKeyLabel.trim(), api_key: newKeyValue.trim() }),
      })
      setNewKeyLabel(''); setNewKeyValue('')
      const d = await fetch(`${API}/api/admin/gemini-keys`).then(r => r.json())
      setGeminiKeys(d.keys || []); setPoolSize(d.pool_size || 0)
    } finally { setKeyLoading(false) }
  }

  const toggleKey = async (id: string, is_active: boolean) => {
    await fetch(`${API}/api/admin/gemini-keys/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active }),
    })
    setGeminiKeys(prev => prev.map(k => k.id === id ? { ...k, is_active } : k))
  }

  const deleteKey = async (id: string) => {
    if (!confirm('Bu key silinsin mi?')) return
    await fetch(`${API}/api/admin/gemini-keys/${id}`, { method: 'DELETE' })
    setGeminiKeys(prev => prev.filter(k => k.id !== id))
  }

  const handleDeleteSession = async (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation()
    if (!confirm(`"${name}" analizini silmek istediğine emin misin?`)) return
    setDeletingId(id)
    try {
      await adminDeleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch {
      alert('Silinemedi')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <>
      <PageHeader
        title="Admin Paneli"
        description="Müşteriler, analizler, kredi yönetimi"
        actions={<Badge tone="brand" soft>Internal</Badge>}
      />

      {/* ── KPI'lar ── */}
      <div className="kpi-grid">
        {[
          { label: 'Kayıtlı Müşteri', val: kpis.users, sub: 'Toplam kullanıcı' },
          { label: 'Firma Profili', val: kpis.firms, sub: 'Onboarding tamamlayan' },
          { label: 'Analiz Oturumu', val: kpis.sessions, sub: 'Tüm zamanlar' },
          { label: 'Toplam Kredi', val: kpis.totalCredits.toLocaleString('tr-TR'), sub: 'Kullanıcılarda kalan' },
        ].map(k => (
          <Card key={k.label} variant="elevated" padding="md">
            <div className="kpi">
              <span className="kpi-label">{k.label}</span>
              <div className="kpi-val">{typeof k.val === 'number' ? k.val.toLocaleString('tr-TR') : k.val}</div>
              <span className="kpi-sub">{k.sub}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* ── Gemini Key Yönetimi ── */}
      <section className="sec">
        <div className="sec-head">
          <h2>Gemini API Key Havuzu</h2>
          <Badge tone={poolSize > 0 ? 'success' : 'danger'} dot soft>
            {poolSize > 0 ? `${poolSize} key aktif` : 'Key yok'}
          </Badge>
        </div>
        <Card padding="md">
          <div className="key-list">
            {geminiKeys.length === 0 && (
              <p className="muted" style={{margin:0}}>Henüz key eklenmedi. Aşağıdan ekleyin.</p>
            )}
            {geminiKeys.map(k => (
              <div key={k.id} className="key-row">
                <div className="key-info">
                  <span className="key-label">{k.label}</span>
                  <span className="key-mask">{k.api_key_masked}</span>
                </div>
                <div className="key-actions">
                  <Badge tone={k.is_active ? 'success' : 'neutral'} soft dot>
                    {k.is_active ? 'Aktif' : 'Pasif'}
                  </Badge>
                  <button className="key-btn" onClick={() => toggleKey(k.id, !k.is_active)}>
                    {k.is_active ? 'Durdur' : 'Aktif Et'}
                  </button>
                  <button className="key-btn danger" onClick={() => deleteKey(k.id)}>Sil</button>
                </div>
              </div>
            ))}
          </div>
          <div className="key-add">
            <input
              className="key-input"
              placeholder="Key adı (ör: Key 1)"
              value={newKeyLabel}
              onChange={e => setNewKeyLabel(e.target.value)}
            />
            <input
              className="key-input"
              placeholder="AIzaSy..."
              value={newKeyValue}
              onChange={e => setNewKeyValue(e.target.value)}
              type="password"
            />
            <Button variant="primary" size="sm" onClick={addKey} loading={keyLoading}
              disabled={!newKeyLabel.trim() || !newKeyValue.trim()}>
              + Ekle
            </Button>
          </div>
        </Card>
      </section>

      {/* ── Müşteri Kartları ── */}
      <section className="sec">
        <div className="sec-head">
          <h2>Müşteriler</h2>
          <span className="muted">{customers.length} kullanıcı</span>
        </div>
        {customers.length === 0 ? (
          <EmptyState title="Henüz müşteri yok" description="Kayıt olan kullanıcılar burada görünecek." />
        ) : (
          <div className="customer-grid">
            {customers.map(c => (
              <div key={c.id} className="customer-card" onClick={() => router.push(`/admin/customers/${c.id}`)}>
                <div className="cc-top">
                  <div className="cc-avatar">
                    {(c.full_name || c.email || '?')[0].toUpperCase()}
                  </div>
                  <div className="cc-info">
                    <div className="cc-name">{c.full_name || '—'}</div>
                    <div className="cc-email">{c.email}</div>
                  </div>
                  <Badge
                    tone={c.org ? 'success' : 'warning'}
                    soft
                  >
                    {c.org ? 'Aktif' : 'Onboarding yok'}
                  </Badge>
                </div>

                <div className="cc-body">
                  {c.org && (
                    <div className="cc-row">
                      <span className="cc-lbl">Firma</span>
                      <span className="cc-val">{c.org.company_name}</span>
                    </div>
                  )}
                  {c.org?.domain_url && (
                    <div className="cc-row">
                      <span className="cc-lbl">Website</span>
                      <span className="cc-val link">{c.org.domain_url}</span>
                    </div>
                  )}
                  <div className="cc-row">
                    <span className="cc-lbl">Kredi</span>
                    <span className={`cc-val ${c.credits < 3 ? 'warn' : 'ok'}`}>
                      {c.credits} kredi
                    </span>
                  </div>
                  <div className="cc-row">
                    <span className="cc-lbl">Analiz</span>
                    <span className="cc-val">{c.session_count} oturum</span>
                  </div>
                  <div className="cc-row">
                    <span className="cc-lbl">Son giriş</span>
                    <span className="cc-val">{timeAgo(c.last_sign_in_at)}</span>
                  </div>
                  <div className="cc-row">
                    <span className="cc-lbl">Kayıt</span>
                    <span className="cc-val">{new Date(c.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  </div>
                </div>

                <div className="cc-footer">
                  <Button variant="ghost" size="sm">Detay & Kredi Yükle →</Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Son Analizler ── */}
      <section className="sec">
        <div className="sec-head">
          <h2>Son Analizler</h2>
          <span className="muted">{sessions.length} kayıt</span>
        </div>
        {sessions.length === 0 ? (
          <EmptyState title="Henüz analiz yok" description="Müşteriler oturum başlattıkça burada görünecek." />
        ) : (
          <Card padding="none">
            <table className="tbl">
              <thead>
                <tr>
                  <th>İş</th><th>Firma</th><th>Durum</th><th>İlerleme</th><th>Süre</th><th>Tarih</th><th></th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => {
                  const st = s.status as string
                  return (
                    <tr key={s.id}>
                      <td className="primary">
                        {s.job_name}
                        {st === 'failed' && s.error_message && (
                          <div className="err-msg" title={s.error_message}>⚠ {s.error_message}</div>
                        )}
                      </td>
                      <td>{firmName(s)}</td>
                      <td>
                        <Badge tone={st === 'completed' ? 'success' : st === 'processing' ? 'info' : st === 'failed' ? 'danger' : 'neutral'} dot>
                          {st === 'completed' ? 'Tamamlandı' : st === 'processing' ? 'İşleniyor' : st === 'pending' ? 'Bekliyor' : 'Hata'}
                        </Badge>
                      </td>
                      <td>{s.processed_products}/{s.total_products}</td>
                      <td className="td-dur">
                        <span>{fmtDuration(s.created_at, s.completed_at)}</span>
                        {s.processed_products > 0 && s.completed_at && (
                          <span className="td-avg">{avgPerProduct(s.created_at, s.completed_at, s.processed_products)}</span>
                        )}
                      </td>
                      <td>{new Date(s.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                      <td className="tbl-actions">
                        <Button variant="ghost" size="sm" onClick={() => router.push(`/seo/session/${s.id}`)}>Gör →</Button>
                        <button
                          className="del-btn"
                          onClick={(e) => handleDeleteSession(e, s.id, s.job_name)}
                          disabled={deletingId === s.id}
                          title="Sil"
                        >
                          {deletingId === s.id
                            ? <span className="del-spin" />
                            : <svg width="13" height="13" viewBox="0 0 14 14" fill="none"><path d="M3 4H11M5.5 4V2.5C5.5 2.22 5.72 2 6 2H8C8.28 2 8.5 2.22 8.5 2.5V4M4 4L4.5 11.5C4.53 11.78 4.76 12 5.05 12H8.95C9.24 12 9.47 11.78 9.5 11.5L10 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                          }
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Card>
        )}
      </section>

      {/* ── Sektör Yönetimi ── */}
      <SectorManager />

      <style jsx>{`
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
        .kpi { display: flex; flex-direction: column; gap: 4px; }
        .kpi-label { font-size: var(--text-xs); color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: var(--weight-medium); }
        .kpi-val { font-size: var(--text-3xl); font-weight: var(--weight-bold); color: var(--text-primary); line-height: 1.1; }
        .kpi-sub { font-size: var(--text-xs); color: var(--text-tertiary); }

        .sec { margin-bottom: 40px; }
        .sec-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
        .sec-head h2 { font-size: var(--text-xl); font-weight: var(--weight-semibold); margin: 0; }
        .muted { font-size: var(--text-xs); color: var(--text-tertiary); }

        /* ── Gemini Keys ── */
        .key-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
        .key-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; background: var(--surface-2); border-radius: var(--radius-md); gap: 12px; }
        .key-info { display: flex; flex-direction: column; gap: 2px; }
        .key-label { font-size: var(--text-sm); font-weight: var(--weight-medium); color: var(--text-primary); }
        .key-mask { font-size: var(--text-xs); color: var(--text-tertiary); font-family: monospace; }
        .key-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
        .key-btn { padding: 4px 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-default); background: transparent; color: var(--text-secondary); font-size: var(--text-xs); cursor: pointer; transition: all var(--duration-fast); }
        .key-btn:hover { background: var(--surface-3); }
        .key-btn.danger { color: var(--error-text, #ef4444); border-color: rgba(239,68,68,0.3); }
        .key-btn.danger:hover { background: var(--error-subtle, rgba(239,68,68,0.08)); }
        .key-add { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; }
        .key-input { flex: 1; min-width: 120px; padding: 8px 12px; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-2); color: var(--text-primary); font-size: var(--text-sm); outline: none; }
        .key-input:focus { border-color: var(--brand-primary); box-shadow: 0 0 0 3px var(--brand-subtle); }

        /* ── Customer Cards ── */
        .customer-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
        .customer-card {
          background: var(--surface-1);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 20px;
          cursor: pointer;
          transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
          display: flex; flex-direction: column; gap: 16px;
        }
        .customer-card:hover {
          border-color: var(--brand-border);
          box-shadow: 0 4px 16px rgba(99,102,241,0.08);
        }
        .cc-top { display: flex; align-items: center; gap: 12px; }
        .cc-avatar {
          width: 40px; height: 40px; border-radius: 50%;
          background: var(--brand-gradient);
          color: white; font-weight: 700; font-size: var(--text-base);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .cc-info { flex: 1; min-width: 0; }
        .cc-name { font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .cc-email { font-size: var(--text-xs); color: var(--text-tertiary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .cc-body { display: flex; flex-direction: column; gap: 8px; }
        .cc-row { display: flex; justify-content: space-between; align-items: center; font-size: var(--text-xs); }
        .cc-lbl { color: var(--text-tertiary); }
        .cc-val { color: var(--text-secondary); font-weight: var(--weight-medium); }
        .cc-val.link { color: var(--brand-text); }
        .cc-val.ok { color: var(--success-text); }
        .cc-val.warn { color: var(--warning-text); }
        .cc-footer { border-top: 1px solid var(--border-subtle); padding-top: 12px; }

        /* ── Table ── */
        .tbl { width: 100%; border-collapse: collapse; }
        .tbl th { text-align: left; font-size: var(--text-xs); font-weight: var(--weight-medium); color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 16px; border-bottom: 1px solid var(--border-subtle); }
        .tbl td { padding: 12px 16px; border-bottom: 1px solid var(--border-subtle); font-size: var(--text-sm); color: var(--text-secondary); }
        .tbl tr:last-child td { border-bottom: none; }
        .tbl td.primary { color: var(--text-primary); font-weight: var(--weight-medium); }
        .err-msg { font-size: var(--text-xs); color: var(--error-text, #ef4444); font-weight: var(--weight-normal); margin-top: 2px; max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .td-dur { display: flex; flex-direction: column; gap: 1px; }
        .td-avg { font-size: var(--text-xs); color: var(--text-tertiary); }
        .tbl-actions { display: flex; align-items: center; gap: 4px; }
        .del-btn {
          display: inline-flex; align-items: center; justify-content: center;
          width: 26px; height: 26px;
          border: 1px solid var(--border-subtle); background: transparent;
          border-radius: var(--radius-sm); color: var(--text-tertiary);
          cursor: pointer; transition: all var(--duration-fast);
          flex-shrink: 0;
        }
        .del-btn:hover:not(:disabled) { border-color: var(--error-border, #ef4444); color: var(--error-text, #ef4444); background: var(--error-subtle, rgba(239,68,68,0.08)); }
        .del-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .del-spin { display: inline-block; width: 10px; height: 10px; border: 1.5px solid rgba(0,0,0,0.15); border-top-color: currentColor; border-radius: 50%; animation: spin 0.6s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }

        @media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 600px) { .kpi-grid { grid-template-columns: 1fr; } }
      `}</style>
    </>
  )
}

// ──────────────── SEKTÖR YÖNETİMİ BİLEŞENİ ────────────────

const DATA_TYPES = ['keywords', 'faq', 'schema', 'competitor', 'seasonal'] as const
const DATA_TYPE_LABELS: Record<string, string> = {
  keywords: 'Anahtar Kelimeler',
  faq: 'FAQ Kalıpları',
  schema: 'Schema Markup',
  competitor: 'Rakip Analizi',
  seasonal: 'Mevsimsel',
}

interface SectorRow { id: string; slug: string; display_name: string }
interface IntelRow { id: string; sector_id: string; data_type: string; content: unknown; quality_score: number; source: string; updated_at: string }

function SectorManager() {
  const supabase = createClient()
  const [sectors, setSectors] = useState<SectorRow[]>([])
  const [selected, setSelected] = useState<string>('')
  const [intels, setIntels] = useState<IntelRow[]>([])
  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)
  const [newType, setNewType] = useState<string>('keywords')
  const [newContent, setNewContent] = useState('')
  const [newScore, setNewScore] = useState(7)
  const [jsonError, setJsonError] = useState('')
  const [crawling, setCrawling] = useState(false)
  const [crawlResult, setCrawlResult] = useState<{ status: string; layers?: string[]; quality?: number; error?: string } | null>(null)

  useEffect(() => {
    supabase.from('sectors').select('id,slug,display_name').eq('aktif', true).order('display_name')
      .then(({ data }) => { if (data) { setSectors(data); if (data[0]) setSelected(data[0].id) } })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    supabase.from('sector_intelligence')
      .select('*').eq('sector_id', selected).order('data_type').order('quality_score', { ascending: false })
      .then(({ data }) => { setIntels(data || []) })
      .then(() => setLoading(false), () => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected])

  const saveIntel = async () => {
    setJsonError('')
    let parsed: unknown
    try { parsed = JSON.parse(newContent) } catch { setJsonError('Geçersiz JSON — düzeltin'); return }
    setAdding(true)
    const { error } = await supabase.from('sector_intelligence').insert({
      sector_id: selected,
      data_type: newType,
      content: parsed,
      quality_score: newScore,
      source: 'admin',
    })
    if (!error) {
      setNewContent('')
      const { data } = await supabase.from('sector_intelligence')
        .select('*').eq('sector_id', selected).order('data_type').order('quality_score', { ascending: false })
      setIntels(data || [])
    }
    setAdding(false)
  }

  const deleteIntel = async (id: string) => {
    if (!confirm('Bu veri silinsin mi?')) return
    await supabase.from('sector_intelligence').delete().eq('id', id)
    setIntels(prev => prev.filter(i => i.id !== id))
  }

  const startCrawl = async () => {
    const sector = sectors.find(s => s.id === selected)
    if (!sector) return
    setCrawling(true)
    setCrawlResult(null)
    try {
      const res = await fetch(`${API}/api/admin/sector/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sector_id: sector.id,
          sector_slug: sector.slug,
          sector_name: sector.display_name,
        }),
      })
      const data = await res.json()
      if (data.status === 'queued' || data.status === 'already_running') {
        // Tarama arka planda — 45 saniye sonra durum kontrolü yap
        setCrawlResult({ status: 'running' })
        setTimeout(async () => {
          const statusRes = await fetch(`${API}/api/admin/sector/crawl/${sector.id}`)
          const statusData = await statusRes.json()
          setCrawlResult({
            status: statusData.status,
            layers: statusData.saved_layers,
            quality: statusData.quality_score,
            error: statusData.error,
          })
          // Tamamlandıysa listeyi yenile
          if (statusData.status === 'completed') {
            const { data: fresh } = await supabase.from('sector_intelligence')
              .select('*').eq('sector_id', selected).order('data_type').order('quality_score', { ascending: false })
            setIntels(fresh || [])
          }
          setCrawling(false)
        }, 45000)
      } else {
        setCrawlResult({ status: 'error', error: data.message })
        setCrawling(false)
      }
    } catch (err) {
      setCrawlResult({ status: 'error', error: String(err) })
      setCrawling(false)
    }
  }

  const currentSector = sectors.find(s => s.id === selected)

  const JSON_TEMPLATES: Record<string, string> = {
    keywords: JSON.stringify({ clusters: [{ intent: "transactional", keywords: ["pamuklu sütyen satın al", "balensiz sütyen fiyatları"], difficulty: "medium" }] }, null, 2),
    faq: JSON.stringify({ questions: [{ soru: "Pamuklu sütyen nasıl seçilir?", cevap_tipi: "rehber", intent: "informational" }] }, null, 2),
    schema: JSON.stringify({ types: ["Product", "ItemPage"], tips: ["AggregateRating ekle", "breadcrumb kullan"] }, null, 2),
    competitor: JSON.stringify({ sites: [{ url: "rakip.com", title_pattern: "[Marka] [Ürün] - [Özellik] | Fiyat", meta_pattern: "✓ Ücretsiz Kargo ✓ 30 Gün İade" }] }, null, 2),
    seasonal: JSON.stringify({ peaks: [{ month: "Şubat", keywords: ["sevgililer günü sütyen seti"], uplift: "+40%" }] }, null, 2),
  }

  return (
    <section className="sec">
      <div className="sec-head">
        <h2>Sektör İstihbarat Yönetimi</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Badge tone="brand" soft>{intels.length} veri katmanı</Badge>
          {selected && (
            <Button
              variant="secondary"
              size="sm"
              onClick={startCrawl}
              loading={crawling}
              disabled={crawling}
            >
              {crawling ? 'Taranıyor...' : '🔍 Otomatik Tara'}
            </Button>
          )}
        </div>
      </div>

      {/* Tarama sonuç bandı */}
      {crawlResult && (
        <div style={{
          padding: '10px 14px',
          borderRadius: 'var(--radius-md)',
          marginBottom: 12,
          fontSize: 'var(--text-sm)',
          background: crawlResult.status === 'completed'
            ? 'rgba(34,197,94,0.1)'
            : crawlResult.status === 'error'
            ? 'rgba(239,68,68,0.1)'
            : 'rgba(var(--brand-rgb),0.1)',
          border: `1px solid ${crawlResult.status === 'completed' ? 'rgba(34,197,94,0.3)' : crawlResult.status === 'error' ? 'rgba(239,68,68,0.3)' : 'var(--brand-border)'}`,
          color: 'var(--text-primary)',
        }}>
          {crawlResult.status === 'running' && '⏳ Tarama arka planda devam ediyor (~45sn)...'}
          {crawlResult.status === 'completed' && (
            <>✅ Tarama tamamlandı — {crawlResult.layers?.join(', ')} katmanları kaydedildi · Kalite skoru: {crawlResult.quality}/10</>
          )}
          {crawlResult.status === 'error' && `❌ Hata: ${crawlResult.error}`}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {sectors.map(s => (
          <button
            key={s.id}
            onClick={() => setSelected(s.id)}
            style={{
              padding: '6px 14px', borderRadius: 999, fontSize: 'var(--text-sm)',
              border: `1px solid ${selected === s.id ? 'var(--brand-border)' : 'var(--border-default)'}`,
              background: selected === s.id ? 'var(--brand-subtle)' : 'var(--surface-1)',
              color: selected === s.id ? 'var(--brand-text)' : 'var(--text-secondary)',
              cursor: 'pointer', fontWeight: selected === s.id ? 600 : 400,
            }}
          >{s.display_name}</button>
        ))}
      </div>

      {selected && (
        <>
          {/* Mevcut veriler */}
          <Card padding="md">
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', margin: '0 0 12px' }}>
              <strong style={{ color: 'var(--text-primary)' }}>{currentSector?.display_name}</strong> sektörü için mevcut istihbarat katmanları
            </p>
            {loading ? <p className="muted">Yükleniyor...</p> : intels.length === 0 ? (
              <p className="muted">Bu sektör için henüz veri eklenmedi.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {intels.map(intel => (
                  <div key={intel.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: 'var(--surface-2)', borderRadius: 'var(--radius-md)' }}>
                    <Badge tone="brand" soft>{DATA_TYPE_LABELS[intel.data_type] || intel.data_type}</Badge>
                    <Badge tone={intel.quality_score >= 7 ? 'success' : 'warning'} soft>Q:{intel.quality_score}</Badge>
                    <Badge tone="neutral" soft>{intel.source}</Badge>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', flex: 1 }}>
                      {new Date(intel.updated_at).toLocaleDateString('tr-TR')}
                    </span>
                    <button
                      onClick={() => deleteIntel(intel.id)}
                      style={{ padding: '3px 8px', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, background: 'transparent', color: '#ef4444', fontSize: 'var(--text-xs)', cursor: 'pointer' }}
                    >Sil</button>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Yeni veri ekle */}
          <Card padding="md" style={{ marginTop: 12 }}>
            <p style={{ fontWeight: 600, fontSize: 'var(--text-sm)', margin: '0 0 12px' }}>Yeni Veri Ekle</p>
            <div style={{ display: 'flex', gap: 10, marginBottom: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <select
                value={newType}
                onChange={e => { setNewType(e.target.value); setNewContent(JSON_TEMPLATES[e.target.value] || ''); setJsonError('') }}
                style={{ padding: '7px 10px', background: 'var(--surface-2)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}
              >
                {DATA_TYPES.map(t => <option key={t} value={t}>{DATA_TYPE_LABELS[t]}</option>)}
              </select>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>Kalite (0-10):</label>
                <input
                  type="number" min={0} max={10} value={newScore}
                  onChange={e => setNewScore(Number(e.target.value))}
                  style={{ width: 54, padding: '6px 8px', background: 'var(--surface-2)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: 'var(--text-sm)' }}
                />
              </div>
              <button
                onClick={() => setNewContent(JSON_TEMPLATES[newType] || '{}')}
                style={{ padding: '6px 12px', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', color: 'var(--text-tertiary)', fontSize: 'var(--text-xs)', cursor: 'pointer' }}
              >Şablon</button>
            </div>
            <textarea
              value={newContent || JSON_TEMPLATES[newType]}
              onChange={e => { setNewContent(e.target.value); setJsonError('') }}
              rows={10}
              placeholder="JSON formatında veri girin..."
              style={{ width: '100%', padding: '10px 12px', background: 'var(--surface-2)', border: `1px solid ${jsonError ? '#ef4444' : 'var(--border-default)'}`, borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: 'var(--text-xs)', fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box' }}
            />
            {jsonError && <p style={{ color: '#ef4444', fontSize: 'var(--text-xs)', margin: '4px 0 0' }}>{jsonError}</p>}
            <div style={{ marginTop: 10, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="gradient" onClick={saveIntel} loading={adding} size="sm">Kaydet</Button>
            </div>
          </Card>
        </>
      )}
    </section>
  )
}
