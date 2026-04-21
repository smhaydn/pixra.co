'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const router = useRouter()
  const supabase = createClient()

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    if (isSignUp) {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) {
        setError(error.message)
      } else {
        setSuccess('Kayıt başarılı! E-postanızı kontrol edip hesabınızı doğrulayın.')
      }
    } else {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) {
        setError('E-posta veya şifre hatalı.')
      } else {
        router.push('/')
        router.refresh()
      }
    }

    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="login-left-content">
          <div className="brand">
            <div className="brand-icon">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <path d="M4 14L10.5 20.5L24 7" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span className="brand-name">Pixra</span>
          </div>
          <div className="trust-badge">
            <span className="gift">🎁</span>
            <span>İlk <strong>10 ürün analizi</strong> ücretsiz — kredi kartı gerekmez</span>
          </div>
          <h1>E-ticaret ürünlerinizi<br /><span className="gradient-text">yapay zeka ile</span> optimize edin</h1>
          <p className="subtitle">
            SEO başlık, açıklama, anahtar kelimeler ve Google Shopping alanlarını
            tek tıkla oluşturun. Ticimax entegrasyonu ile doğrudan mağazanıza aktarın.
          </p>
          <div className="features">
            <div className="feature">
              <span className="feature-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8L6 12L14 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </span>
              <span>Toplu ürün analizi ve SEO/GEO içerik üretimi</span>
            </div>
            <div className="feature">
              <span className="feature-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8L6 12L14 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </span>
              <span>Ticimax'e otomatik aktarım</span>
            </div>
            <div className="feature">
              <span className="feature-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8L6 12L14 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </span>
              <span>Google Shopping / Adwords uyumlu çıktılar</span>
            </div>
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-form-wrapper">
          <div className="form-header">
            <h2>{isSignUp ? 'Hesap Oluştur' : 'Giriş Yap'}</h2>
            <p>{isSignUp ? '10 ücretsiz analiz ile başla — kredi kartı gerekmez' : 'Hesabınıza giriş yapın'}</p>
          </div>

          <form className="form" onSubmit={handleAuth}>
            <div className="field">
              <label htmlFor="email">E-posta</label>
              <input
                id="email"
                type="email"
                placeholder="ornek@firma.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="field">
              <div className="label-row">
                <label htmlFor="password">Şifre</label>
                {!isSignUp && (
                  <Link href="/forgot-password" className="forgot-link">Şifremi unuttum</Link>
                )}
              </div>
              <input
                id="password"
                type="password"
                placeholder="Minimum 6 karakter"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={isSignUp ? 'new-password' : 'current-password'}
              />
            </div>

            {error && <div className="alert alert-error">{error}</div>}
            {success && <div className="alert alert-success">{success}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? (
                <span className="spinner" />
              ) : isSignUp ? (
                'Hesap Oluştur'
              ) : (
                'Giriş Yap'
              )}
            </button>
          </form>

          <div className="switch-mode">
            {isSignUp ? (
              <span>Zaten hesabınız var mı? <button onClick={() => { setIsSignUp(false); setError(''); setSuccess('') }}>Giriş Yap</button></span>
            ) : (
              <span>Hesabınız yok mu? <button onClick={() => { setIsSignUp(true); setError(''); setSuccess('') }}>Kayıt Ol</button></span>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .login-page {
          display: flex;
          min-height: 100vh;
          background: var(--surface-0);
        }

        /* ── Left Panel ── */
        .login-left {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px;
          background: var(--surface-1);
          border-right: 1px solid var(--border-subtle);
        }
        .login-left-content {
          max-width: 480px;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 40px;
        }
        .trust-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: var(--brand-subtle);
          border: 1px solid var(--brand-border);
          color: var(--brand-text);
          border-radius: 999px;
          font-size: 0.82rem;
          font-weight: 500;
          margin-bottom: 24px;
        }
        .trust-badge strong { font-weight: 700; }
        .trust-badge .gift { font-size: 1rem; }
        .gradient-text {
          background: var(--brand-gradient);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .brand-icon {
          width: 40px;
          height: 40px;
          background: var(--brand-gradient);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .brand-name {
          font-size: 1.4rem;
          font-weight: 700;
          color: var(--text-primary);
          letter-spacing: -0.3px;
        }
        .login-left h1 {
          font-size: 2.2rem;
          font-weight: 700;
          line-height: 1.25;
          color: var(--text-primary);
          margin: 0 0 16px;
          letter-spacing: -0.5px;
        }
        .subtitle {
          color: var(--text-secondary);
          font-size: 0.95rem;
          line-height: 1.6;
          margin: 0 0 32px;
        }
        .features {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .feature {
          display: flex;
          align-items: center;
          gap: 10px;
          color: var(--text-secondary);
          font-size: 0.88rem;
        }
        .feature-icon {
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--success-text);
          flex-shrink: 0;
        }

        /* ── Right Panel ── */
        .login-right {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px;
        }
        .login-form-wrapper {
          width: 100%;
          max-width: 380px;
        }
        .form-header {
          margin-bottom: 32px;
        }
        .form-header h2 {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0 0 6px;
        }
        .form-header p {
          color: var(--text-tertiary);
          font-size: 0.9rem;
          margin: 0;
        }

        /* ── Form ── */
        .form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .field label {
          color: var(--text-secondary);
          font-size: 0.8rem;
          font-weight: 500;
        }
        .label-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .forgot-link {
          color: var(--brand-text);
          text-decoration: none;
          font-size: 0.78rem;
          font-weight: 500;
        }
        .forgot-link:hover {
          text-decoration: underline;
        }
        .field input {
          padding: 10px 14px;
          border-radius: var(--radius-md);
          border: 1px solid var(--border-default);
          background: var(--surface-2);
          color: var(--text-primary);
          font-size: 0.9rem;
          outline: none;
          transition: border-color var(--duration-fast) var(--ease-out),
                      box-shadow var(--duration-fast) var(--ease-out);
        }
        .field input::placeholder {
          color: var(--text-muted);
        }
        .field input:focus {
          border-color: var(--brand-primary);
          box-shadow: 0 0 0 3px var(--brand-subtle);
        }

        /* ── Alerts ── */
        .alert {
          padding: 10px 14px;
          border-radius: var(--radius-md);
          font-size: 0.85rem;
          font-weight: 500;
          animation: slideUp var(--duration-base) var(--ease-out);
        }
        .alert-error {
          background: var(--error-subtle);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: var(--error-text);
        }
        .alert-success {
          background: var(--success-subtle);
          border: 1px solid rgba(34, 197, 94, 0.2);
          color: var(--success-text);
        }

        /* ── Submit ── */
        .submit-btn {
          padding: 11px 16px;
          border: none;
          border-radius: var(--radius-md);
          background: var(--brand-gradient);
          color: white;
          font-size: 0.9rem;
          font-weight: 600;
          cursor: pointer;
          transition: background var(--duration-fast) var(--ease-out),
                      box-shadow var(--duration-fast) var(--ease-out);
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 42px;
        }
        .submit-btn:hover:not(:disabled) {
          background: var(--brand-hover);
          box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
        }
        .submit-btn:active:not(:disabled) {
          transform: scale(0.98);
        }
        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* ── Spinner ── */
        .spinner {
          display: inline-block;
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255, 255, 255, 0.25);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }

        /* ── Switch Mode ── */
        .switch-mode {
          margin-top: 24px;
          text-align: center;
          font-size: 0.85rem;
          color: var(--text-tertiary);
        }
        .switch-mode button {
          background: none;
          border: none;
          color: var(--brand-text);
          cursor: pointer;
          font-weight: 600;
          font-size: 0.85rem;
          padding: 0;
        }
        .switch-mode button:hover {
          color: var(--brand-primary);
          text-decoration: underline;
        }

        /* ── Responsive ── */
        @media (max-width: 900px) {
          .login-page {
            flex-direction: column;
          }
          .login-left {
            padding: 32px 24px;
            border-right: none;
            border-bottom: 1px solid var(--border-subtle);
          }
          .login-left h1 {
            font-size: 1.6rem;
          }
          .login-right {
            padding: 32px 24px;
          }
        }

        @media (max-width: 600px) {
          .login-left {
            display: none;
          }
          .login-right {
            padding: 24px 20px;
          }
          .login-form-wrapper {
            max-width: 100%;
          }
          .form-header {
            text-align: center;
          }
        }
      `}</style>
    </div>
  )
}
