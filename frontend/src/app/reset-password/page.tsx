'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function ResetPasswordPage() {
  const router = useRouter()
  const supabase = createClient()

  const [checking, setChecking] = useState(true)
  const [validSession, setValidSession] = useState(false)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setValidSession(!!user)
      setChecking(false)
    })
  }, [supabase])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password.length < 6) return setError('Şifre en az 6 karakter olmalı')
    if (password !== confirm) return setError('Şifreler eşleşmiyor')

    setLoading(true)
    const { error } = await supabase.auth.updateUser({ password })
    setLoading(false)

    if (error) {
      setError(error.message)
      return
    }

    setDone(true)
    setTimeout(() => router.push('/'), 1500)
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

        {checking ? (
          <div className="loading">
            <span className="spinner big" />
            <p>Oturum doğrulanıyor…</p>
          </div>
        ) : !validSession ? (
          <>
            <div className="icon-done">⚠️</div>
            <h1>Link geçersiz veya süresi dolmuş</h1>
            <p className="muted">
              Bu şifre sıfırlama linki çalışmıyor. Link süresi 1 saat ile sınırlı; yeni bir tane iste.
            </p>
            <Link href="/forgot-password" className="link-btn">Yeni Link Gönder</Link>
          </>
        ) : done ? (
          <>
            <div className="icon-done">✅</div>
            <h1>Şifren güncellendi</h1>
            <p className="muted">Panele yönlendiriliyorsun…</p>
          </>
        ) : (
          <>
            <h1>Yeni şifre belirle</h1>
            <p className="muted">Hesabın için yeni bir şifre seç. En az 6 karakter.</p>

            <form onSubmit={submit} className="form">
              <div className="field">
                <label htmlFor="pw">Yeni Şifre</label>
                <input
                  id="pw"
                  type="password"
                  placeholder="Minimum 6 karakter"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  minLength={6}
                  autoComplete="new-password"
                  autoFocus
                />
              </div>
              <div className="field">
                <label htmlFor="pw2">Şifre Tekrar</label>
                <input
                  id="pw2"
                  type="password"
                  placeholder="Aynı şifreyi tekrar gir"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  required
                  minLength={6}
                  autoComplete="new-password"
                />
              </div>

              {error && <div className="alert">{error}</div>}

              <button type="submit" disabled={loading} className="submit">
                {loading ? <span className="spinner" /> : 'Şifreyi Güncelle'}
              </button>
            </form>
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
        .icon-done {
          font-size: 2.5rem;
          margin-bottom: 8px;
          animation: slideUp var(--duration-slow) var(--ease-out);
        }
        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          padding: 20px 0;
          color: var(--text-tertiary);
          font-size: var(--text-sm);
        }

        .form {
          display: flex;
          flex-direction: column;
          gap: 16px;
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

        .submit, .link-btn {
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
          text-decoration: none;
        }
        .submit:hover:not(:disabled), .link-btn:hover { opacity: 0.9; }
        .submit:disabled { opacity: 0.6; cursor: not-allowed; }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }
        .spinner.big {
          width: 28px;
          height: 28px;
          border-color: var(--border-default);
          border-top-color: var(--brand-primary);
        }
      `}</style>
    </div>
  )
}
