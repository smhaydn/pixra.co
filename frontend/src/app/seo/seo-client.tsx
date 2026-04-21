'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Badge, EmptyState, Progress, useToast } from '@/components/ui'
import { PageHeader } from '@/components/shell/AppShell'

interface Firm {
  id: string
  company_name: string
  ws_kodu: string | null
  domain_url: string | null
  gemini_api_key: string | null
}

interface Session {
  id: string
  job_name: string
  status: string
  total_products: number
  processed_products: number
  created_at: string
}

interface SeoClientProps {
  firm: Firm | null
  sessions: Session[]
  userId: string
  credits: number
}

export default function SeoClient({ firm, sessions: initialSessions }: SeoClientProps) {
  const router = useRouter()
  const toast = useToast()
  const supabase = createClient()
  const [sessions, setSessions] = useState(initialSessions)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteSession = async (e: React.MouseEvent, s: Session) => {
    e.stopPropagation()
    if (!confirm(`"${s.job_name}" analizini silmek istediğine emin misin? Bu işlem geri alınamaz.`)) return
    setDeletingId(s.id)
    const { error } = await supabase.from('ai_sessions').delete().eq('id', s.id)
    setDeletingId(null)
    if (error) {
      toast.show('Silinemedi: ' + error.message, 'error')
      return
    }
    setSessions(prev => prev.filter(x => x.id !== s.id))
    toast.show('Analiz silindi', 'success')
    router.refresh()
  }

  return (
    <>
      <PageHeader
        title="SEO & İçerik"
        description="AI ile ürün başlıkları, açıklamalar ve SEO alanları üret"
        actions={
          <Button
            variant="gradient"
            onClick={() => router.push('/seo/new')}
            disabled={!firm || !firm.ws_kodu || !firm.domain_url}
            icon={<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 2V12M2 7H12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>}
          >
            Yeni Analiz
          </Button>
        }
      />

      {!firm || !firm.ws_kodu || !firm.domain_url ? (
        <EmptyState
          icon={<svg width="28" height="28" viewBox="0 0 28 28" fill="none"><path d="M14 4V14M14 20V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /><circle cx="14" cy="14" r="11" stroke="currentColor" strokeWidth="1.6" /></svg>}
          title="Ticimax bağlantısı eksik"
          description={!firm?.ws_kodu
            ? 'Ürünleri çekebilmek için Ticimax WS yetki kodunu gir.'
            : 'Ürünleri çekebilmek için mağaza domain adresini gir (ör. www.firman.com).'}
          action={<Button variant="primary" onClick={() => router.push('/settings')}>Ayarlara Git</Button>}
        />
      ) : sessions.length === 0 ? (
        <EmptyState
          icon={<svg width="28" height="28" viewBox="0 0 28 28" fill="none"><path d="M14 4L18 14H10L14 4Z M14 24V16" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" /></svg>}
          title="İlk analizini başlat"
          description="Mağazandan ürünleri çek, istediklerini seç, AI içerik üretsin. 10 ücretsiz kredin var."
          action={<Button variant="gradient" onClick={() => router.push('/seo/new')}>Hemen Dene</Button>}
        />
      ) : (
        <div className="session-list">
          {sessions.map(s => {
            const percent = s.total_products > 0 ? (s.processed_products / s.total_products) * 100 : 0
            const status = s.status as 'pending' | 'processing' | 'completed' | 'failed'
            return (
              <Card key={s.id} padding="md" interactive onClick={() => router.push(`/seo/session/${s.id}`)}>
                <div className="sess">
                  <div className="sess-head">
                    <h3>{s.job_name}</h3>
                    <div className="sess-head-right">
                      <Badge
                        tone={status === 'completed' ? 'success' : status === 'processing' ? 'info' : status === 'failed' ? 'danger' : (s.status as string) === 'cancelled' ? 'warning' : 'neutral'}
                        dot
                      >
                        {status === 'completed' && 'Tamamlandı'}
                        {status === 'processing' && 'İşleniyor'}
                        {status === 'pending' && 'Bekliyor'}
                        {status === 'failed' && 'Hata'}
                        {(s.status as string) === 'cancelled' && 'Durduruldu'}
                      </Badge>
                      <button
                        type="button"
                        className="sess-delete"
                        aria-label="Analizi sil"
                        onClick={(e) => deleteSession(e, s)}
                        disabled={deletingId === s.id}
                        title="Analizi sil"
                      >
                        {deletingId === s.id ? (
                          <span className="del-spin" />
                        ) : (
                          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 4H11M5.5 4V2.5C5.5 2.22 5.72 2 6 2H8C8.28 2 8.5 2.22 8.5 2.5V4M4 4L4.5 11.5C4.53 11.78 4.76 12 5.05 12H8.95C9.24 12 9.47 11.78 9.5 11.5L10 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                        )}
                      </button>
                    </div>
                  </div>
                  <div className="sess-meta">
                    <span>{s.processed_products}/{s.total_products} ürün</span>
                    <span className="sess-dot">•</span>
                    <span>{new Date(s.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  {status === 'processing' && (
                    <Progress value={percent} tone="brand" showPercent />
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <style jsx>{`
        .session-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .sess {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .sess-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }
        .sess-head h3 {
          font-size: var(--text-base);
          font-weight: var(--weight-semibold);
          margin: 0;
          color: var(--text-primary);
        }
        .sess-meta {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .sess-dot { color: var(--text-muted); }
        .sess-head-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .sess-delete {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          border: 1px solid var(--border-subtle);
          background: transparent;
          border-radius: var(--radius-sm);
          color: var(--text-tertiary);
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
        }
        .sess-delete:hover:not(:disabled) {
          color: var(--error-text);
          border-color: rgba(239, 68, 68, 0.35);
          background: var(--error-subtle);
        }
        .sess-delete:disabled { opacity: 0.5; cursor: not-allowed; }
        .del-spin {
          width: 12px;
          height: 12px;
          border: 2px solid var(--border-default);
          border-top-color: var(--text-tertiary);
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }
      `}</style>
    </>
  )
}
