'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Button, Card, Badge, Input, useToast } from '@/components/ui'
import { PageHeader } from './AppShell'

interface ComingSoonProps {
  module: string
  icon: string
  title: string
  pitch: string
  features: string[]
  userId: string
  email: string
}

export default function ComingSoon({ module, icon, title, pitch, features, userId, email: initialEmail }: ComingSoonProps) {
  const toast = useToast()
  const supabase = createClient()
  const [email, setEmail] = useState(initialEmail)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  const submit = async () => {
    if (!email.trim() || !email.includes('@')) return toast.show('Geçerli bir e-posta gir', 'warning')
    setSubmitting(true)
    await supabase.from('waitlist').insert({
      user_id: userId,
      email,
      package_id: `module:${module}`,
      package_name: title,
    })
    setSubmitting(false)
    setDone(true)
    toast.show('Listeye eklendin — çıktığında ilk sen öğren 🚀', 'success')
  }

  return (
    <>
      <PageHeader title={title} description="Yakında" />

      <div className="cs-grid">
        <Card variant="magic" padding="lg">
          <div className="hero">
            <div className="ico">{icon}</div>
            <Badge tone="info" soft>Yakında</Badge>
            <h2>{title}</h2>
            <p className="pitch">{pitch}</p>
          </div>
        </Card>

        <Card padding="lg">
          <h3>Neler gelecek?</h3>
          <ul className="features">
            {features.map(f => (
              <li key={f}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M3 8L7 12L13 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {f}
              </li>
            ))}
          </ul>
        </Card>

        <Card variant="elevated" padding="lg">
          {done ? (
            <div className="waitlist-done">
              <div className="done-ico">✅</div>
              <h3>Bekleme listesindesin</h3>
              <p>Bu modül hazır olduğunda sana ilk biz haber vereceğiz. Erken kayıt indirimi senin için saklı.</p>
            </div>
          ) : (
            <>
              <h3>Erken erişim al</h3>
              <p className="waitlist-desc">
                Bu modül çıktığında ilk sen dene. Erken kayıt olanlara <strong>%30 indirim</strong> ve ücretsiz kurulum desteği.
              </p>
              <div className="waitlist-form">
                <Input
                  type="email"
                  label="E-posta"
                  placeholder="ornek@firman.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                />
                <Button variant="gradient" onClick={submit} loading={submitting}>
                  Listeye Katıl
                </Button>
              </div>
            </>
          )}
        </Card>
      </div>

      <style jsx>{`
        .cs-grid {
          display: grid;
          grid-template-columns: 1.3fr 1fr;
          grid-template-rows: auto auto;
          gap: 16px;
        }
        .cs-grid > :global(.card:first-child) {
          grid-column: 1 / -1;
        }
        .hero {
          text-align: center;
          padding: 24px 0;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }
        .ico {
          font-size: 3rem;
          animation: glow 3s ease-in-out infinite;
        }
        .hero h2 {
          font-size: var(--text-3xl);
          margin: 0;
          background: var(--brand-gradient);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .pitch {
          color: var(--text-secondary);
          max-width: 560px;
          margin: 0;
          font-size: var(--text-base);
          line-height: 1.6;
        }
        h3 { font-size: var(--text-lg); margin: 0 0 16px; }
        .features {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .features li {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .features svg { color: var(--brand-text); flex-shrink: 0; }
        .waitlist-desc {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          line-height: 1.55;
          margin: 0 0 16px;
        }
        .waitlist-desc strong { color: var(--brand-text); font-weight: var(--weight-semibold); }
        .waitlist-form {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .waitlist-done {
          text-align: center;
          padding: 12px;
        }
        .done-ico {
          font-size: 2.5rem;
          margin-bottom: 8px;
        }
        .waitlist-done p {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          line-height: 1.55;
          margin: 0;
        }
        @media (max-width: 800px) {
          .cs-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </>
  )
}
