'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

type Mode = 'login' | 'signup'

const TR_ERRORS: Record<string, string> = {
  'Invalid login credentials': 'E-posta veya şifre hatalı.',
  'Email not confirmed': 'E-postanızı henüz doğrulamadınız. Gelen kutunuzu kontrol edin.',
  'User already registered': 'Bu e-posta zaten kayıtlı. Giriş yapmayı deneyin.',
  'Password should be at least 6 characters': 'Şifre en az 6 karakter olmalı.',
  'Signup requires a valid password': 'Geçerli bir şifre giriniz.',
  'Email rate limit exceeded': 'Çok fazla deneme yapıldı. Birkaç dakika bekleyip tekrar deneyin.',
  'over_email_send_rate_limit': 'E-posta gönderim limiti aşıldı. Lütfen 1 dakika bekleyin.',
  'email_address_not_authorized': 'Bu e-posta adresi kullanıma kapalı.',
  'weak_password': 'Şifre çok zayıf. Harf, rakam ve özel karakter kullanın.',
}

function mapError(msg: string): string {
  for (const [key, val] of Object.entries(TR_ERRORS)) {
    if (msg.toLowerCase().includes(key.toLowerCase())) return val
  }
  return msg
}

export default function LoginPage() {
  const [mode, setMode] = useState<Mode>('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const router = useRouter()
  const supabase = createClient()

  const switchMode = (m: Mode) => {
    setMode(m)
    setError('')
    setSuccess('')
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    if (mode === 'signup') {
      if (!fullName.trim()) {
        setError('Adınızı ve soyadınızı giriniz.')
        setLoading(false)
        return
      }
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName.trim() },
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) {
        setError(mapError(error.message))
      } else {
        setSuccess('Hesabınız oluşturuldu! E-postanıza bir doğrulama bağlantısı gönderdik. Lütfen gelen kutunuzu kontrol edin.')
      }
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) {
        setError(mapError(error.message))
      } else {
        router.push('/')
        router.refresh()
      }
    }

    setLoading(false)
  }

  return (
    <div className="page">
      <div className="left">
        <div className="left-inner">
          <div className="brand">
            <div className="brand-mark">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M3 13L8 3L13 13H3Z" fill="white" />
              </svg>
            </div>
            <span>Pixra</span>
          </div>

          <div className="pill">
            <span>🎁</span>
            <span>İlk <strong>10 ürün analizi</strong> ücretsiz</span>
          </div>

          <h1>Ürünlerinizi<br /><span className="grad">yapay zeka ile</span><br />öne çıkarın</h1>

          <p className="sub">
            SEO başlık, açıklama ve GEO içerik otomasyonu.
            Ticimax entegrasyonu ile tek tıkla mağazanıza aktarın.
          </p>

          <ul className="feats">
            {[
              'Multi-pass AI içerik motoru',
              'ChatGPT & Perplexity görünürlüğü',
              'Ticimax otomatik aktarım',
              'Schema.org E-E-A-T sinyalleri',
            ].map(f => (
              <li key={f}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7L5.5 10.5L12 3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                {f}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="right">
        <div className="form-card">
          <div className="tabs">
            <button className={mode === 'login' ? 'tab active' : 'tab'} onClick={() => switchMode('login')}>Giriş Yap</button>
            <button className={mode === 'signup' ? 'tab active' : 'tab'} onClick={() => switchMode('signup')}>Kayıt Ol</button>
          </div>

          <div className="form-head">
            <h2>{mode === 'login' ? 'Hoş geldiniz' : 'Hesap oluşturun'}</h2>
            <p>{mode === 'login' ? 'Hesabınıza giriş yapın' : '10 ücretsiz analiz ile başlayın — kredi kartı gerekmez'}</p>
          </div>

          <form onSubmit={handleAuth}>
            {mode === 'signup' && (
              <div className="field">
                <label htmlFor="fullname">Ad Soyad</label>
                <input
                  id="fullname"
                  type="text"
                  placeholder="Örn: Ayşe Kaya"
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  required
                  autoComplete="name"
                />
              </div>
            )}

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
              />
            </div>

            <div className="field">
              <div className="label-row">
                <label htmlFor="password">Şifre</label>
                {mode === 'login' && (
                  <Link href="/forgot-password" className="forgot">Şifremi unuttum</Link>
                )}
              </div>
              <input
                id="password"
                type="password"
                placeholder={mode === 'signup' ? 'En az 6 karakter' : '••••••••'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              />
            </div>

            {error && (
              <div className="alert err">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.4"/><path d="M7 4v3.5M7 10h.01" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
                {error}
              </div>
            )}
            {success && (
              <div className="alert ok">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7L5.5 10.5L12 3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
                {success}
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading
                ? <span className="spin" />
                : mode === 'login' ? 'Giriş Yap' : 'Hesap Oluştur'}
            </button>
          </form>

          <p className="switch">
            {mode === 'login'
              ? <>Hesabınız yok mu? <button onClick={() => switchMode('signup')}>Kayıt Ol</button></>
              : <>Zaten hesabınız var mı? <button onClick={() => switchMode('login')}>Giriş Yap</button></>}
          </p>
        </div>
      </div>

      <style jsx>{`
        .page {
          display: flex;
          min-height: 100vh;
          background: var(--surface-0);
        }

        /* ── Left ── */
        .left {
          flex: 1.1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px;
          background: var(--surface-1);
          border-right: 1px solid var(--border-subtle);
        }
        .left-inner { max-width: 460px; }
        .brand {
          display: flex; align-items: center; gap: 10px;
          font-size: 1.3rem; font-weight: 700; color: var(--text-primary);
          margin-bottom: 36px;
        }
        .brand-mark {
          width: 30px; height: 30px;
          background: var(--brand-gradient);
          border-radius: var(--radius-sm);
          display: flex; align-items: center; justify-content: center;
        }
        .pill {
          display: inline-flex; align-items: center; gap: 8px;
          padding: 7px 14px;
          background: var(--brand-subtle);
          border: 1px solid var(--brand-border);
          border-radius: 999px;
          font-size: 0.82rem; color: var(--brand-text);
          margin-bottom: 24px;
        }
        .pill strong { font-weight: 700; }
        h1 {
          font-size: clamp(1.8rem, 3vw, 2.4rem);
          font-weight: 800; line-height: 1.2;
          color: var(--text-primary); margin: 0 0 16px;
          letter-spacing: -0.5px;
        }
        .grad {
          background: var(--brand-gradient);
          -webkit-background-clip: text; background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .sub {
          color: var(--text-secondary); font-size: 0.95rem;
          line-height: 1.6; margin: 0 0 28px;
        }
        .feats { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
        .feats li {
          display: flex; align-items: center; gap: 10px;
          color: var(--text-secondary); font-size: 0.88rem;
        }
        .feats li svg { color: var(--success-text); flex-shrink: 0; }

        /* ── Right ── */
        .right {
          flex: 1; display: flex;
          align-items: center; justify-content: center;
          padding: 48px;
        }
        .form-card { width: 100%; max-width: 400px; }

        /* ── Tabs ── */
        .tabs {
          display: flex;
          background: var(--surface-2);
          border-radius: var(--radius-md);
          padding: 4px;
          margin-bottom: 28px;
          gap: 4px;
        }
        .tab {
          flex: 1; padding: 8px 0;
          border: none; border-radius: calc(var(--radius-md) - 2px);
          background: transparent;
          color: var(--text-tertiary);
          font-size: 0.88rem; font-weight: 500;
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
        }
        .tab.active {
          background: var(--surface-0);
          color: var(--text-primary);
          font-weight: 600;
          box-shadow: 0 1px 4px rgba(0,0,0,0.15);
        }

        /* ── Form head ── */
        .form-head { margin-bottom: 24px; }
        .form-head h2 {
          font-size: 1.4rem; font-weight: 700;
          color: var(--text-primary); margin: 0 0 4px;
        }
        .form-head p { color: var(--text-tertiary); font-size: 0.86rem; margin: 0; }

        /* ── Fields ── */
        form { display: flex; flex-direction: column; gap: 16px; }
        .field { display: flex; flex-direction: column; gap: 6px; }
        .field label { color: var(--text-secondary); font-size: 0.8rem; font-weight: 500; }
        .label-row { display: flex; justify-content: space-between; align-items: center; }
        .forgot { color: var(--brand-text); text-decoration: none; font-size: 0.78rem; font-weight: 500; }
        .forgot:hover { text-decoration: underline; }
        .field input {
          padding: 10px 14px;
          border-radius: var(--radius-md);
          border: 1px solid var(--border-default);
          background: var(--surface-2);
          color: var(--text-primary);
          font-size: 0.9rem; font-family: inherit;
          outline: none;
          transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
        }
        .field input::placeholder { color: var(--text-muted); }
        .field input:focus {
          border-color: var(--brand-primary);
          box-shadow: 0 0 0 3px var(--brand-subtle);
        }

        /* ── Alerts ── */
        .alert {
          display: flex; align-items: flex-start; gap: 8px;
          padding: 10px 14px;
          border-radius: var(--radius-md);
          font-size: 0.84rem; font-weight: 500; line-height: 1.45;
        }
        .alert svg { flex-shrink: 0; margin-top: 1px; }
        .err { background: var(--error-subtle); border: 1px solid rgba(239,68,68,0.2); color: var(--error-text); }
        .ok { background: var(--success-subtle); border: 1px solid rgba(34,197,94,0.2); color: var(--success-text); }

        /* ── Button ── */
        .btn-primary {
          padding: 11px 16px; border: none;
          border-radius: var(--radius-md);
          background: var(--brand-gradient);
          color: white; font-size: 0.9rem; font-weight: 600;
          cursor: pointer; min-height: 44px;
          display: flex; align-items: center; justify-content: center;
          transition: opacity var(--duration-fast), box-shadow var(--duration-fast);
          margin-top: 4px;
        }
        .btn-primary:hover:not(:disabled) { opacity: 0.9; box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
        .btn-primary:active:not(:disabled) { transform: scale(0.98); }
        .btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }

        .spin {
          display: inline-block; width: 18px; height: 18px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white; border-radius: 50%;
          animation: spin 0.6s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Switch ── */
        .switch {
          margin-top: 20px; text-align: center;
          font-size: 0.84rem; color: var(--text-tertiary);
        }
        .switch button {
          background: none; border: none;
          color: var(--brand-text); font-weight: 600;
          font-size: 0.84rem; cursor: pointer; padding: 0;
        }
        .switch button:hover { text-decoration: underline; }

        /* ── Responsive ── */
        @media (max-width: 900px) {
          .page { flex-direction: column; }
          .left { border-right: none; border-bottom: 1px solid var(--border-subtle); padding: 32px 24px; }
          .right { padding: 32px 24px; }
        }
        @media (max-width: 600px) {
          .left { display: none; }
          .right { padding: 24px 20px; }
        }
      `}</style>
    </div>
  )
}
