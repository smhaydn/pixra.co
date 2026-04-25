'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const supabase = createClient()
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
    })

    setLoading(false)
    if (error) {
      setError(error.message)
    } else {
      setSent(true)
    }
  }

  return (
    <div className="page">
      <div className="card">
        <div className="brand">
          <div className="brand-icon">
            <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
              <path d="M4 14L10.5 20.5L24 7" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span>Pixra</span>
        </div>

        {sent ? (
          <>
            <div className="icon-done">📧</div>
            <h1>E-posta yolda</h1>
            <p className="muted">
              <strong>{email}</strong> adresine şifre sıfırlama linki gönderdik. E-postanı kontrol et,
              linke tıklayarak yeni şifreni belirle.
            </p>
            <p className="hint">
              Birkaç dakika içinde gelmezse spam klasörüne bak. Linkin süresi 1 saat.
            </p>
            <Link href="/login" className="back-link">← Giriş sayfasına dön</Link>
          </>
        ) : (
          <>
            <h1>Şifreni mi unuttun?</h1>
            <p className="muted">Hesabına bağlı e-posta adresini gir, sana sıfırlama linki yollayalım.</p>

            <form onSubmit={submit} className="form">
              <div className="field">
                <label htmlFor="email">E-posta</label>
                <input
                  id="email"
                  type="email"
                  placeholder="ornek@firma.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  autoFocus
                />
              </div>

              {error && <div className="alert">{error}</div>}

              <button type="submit" disabled={loading} className="submit">
                {loading ? <span className="spinner" /> : 'Sıfırlama Linki Gönder'}
              </button>
            </form>

            <Link href="/login" className="back-link">← Giriş yap</Link>
          </>
        )}
      </div>

      <style jsx>{`
        .page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px 20px;
          background: radial-gradient(ellipse at top, rgba(99, 102, 241, 0.08), transparent 60%),
                      var(--surface-0);
        }
        .card {
          width: 100%;
          max-width: 420px;
          background: var(--surface-1);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 40px 32px;
          box-shadow: var(--shadow-lg);
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 10px;
          font-weight: var(--weight-bold);
          margin-bottom: 28px;
        }
        .brand-icon {
          width: 32px;
          height: 32px;
          background: var(--brand-gradient);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        h1 {
          font-size: var(--text-2xl);
          font-weight: var(--weight-bold);
          margin: 0 0 8px;
          letter-spacing: -0.3px;
        }
        .muted {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          line-height: 1.55;
          margin: 0 0 24px;
        }
        .muted strong { color: var(--text-primary); font-weight: var(--weight-semibold); }
        .hint {
          color: var(--text-muted);
          font-size: var(--text-xs);
          margin: 12px 0 24px;
        }
        .icon-done {
          font-size: 2.5rem;
          margin-bottom: 8px;
          animation: slideUp var(--duration-slow) var(--ease-out);
        }

        .form {
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-bottom: 20px;
        }
        .field { display: flex; flex-direction: column; gap: 6px; }
        .field label {
          font-size: var(--text-xs);
          color: var(--text-secondary);
          font-weight: var(--weight-medium);
        }
        .field input {
          padding: 10px 14px;
          border-radius: var(--radius-md);
          border: 1px solid var(--border-default);
          background: var(--surface-2);
          color: var(--text-primary);
          font-size: var(--text-sm);
          outline: none;
          transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
        }
        .field input:focus {
          border-color: var(--brand-primary);
          box-shadow: 0 0 0 3px var(--brand-subtle);
        }

        .alert {
          padding: 10px 14px;
          border-radius: var(--radius-md);
          background: var(--error-subtle);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: var(--error-text);
          font-size: var(--text-sm);
        }

        .submit {
          padding: 11px 16px;
          border: none;
          border-radius: var(--radius-md);
          background: var(--brand-gradient);
          color: white;
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          cursor: pointer;
          min-height: 42px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: opacity var(--duration-fast);
        }
        .submit:hover:not(:disabled) { opacity: 0.9; }
        .submit:disabled { opacity: 0.6; cursor: not-allowed; }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }

        .back-link {
          display: inline-block;
          color: var(--text-tertiary);
          text-decoration: none;
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          margin-top: 8px;
          transition: color var(--duration-fast);
        }
        .back-link:hover { color: var(--brand-text); }
      `}</style>
    </div>
  )
}
