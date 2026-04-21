'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'
import Link from 'next/link'

interface TopBarProps {
  user: User
  role: 'customer' | 'agency' | 'admin'
  credits?: number
  firmName?: string
}

export function TopBar({ user, role, credits = 0, firmName }: TopBarProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  const initial = user.email?.[0]?.toUpperCase() || 'P'
  const lowCredits = credits < 50

  return (
    <header className="topbar">
      <div className="topbar-left">
        {firmName && (
          <div className="firm-tag">
            <div className="firm-dot" />
            <span>{firmName}</span>
          </div>
        )}
      </div>

      <div className="topbar-right">
        <Link href="/credits" className={`credit-pill ${lowCredits ? 'warn' : ''}`} aria-label="Krediler">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
            <path d="M7 1L8.5 5L13 5.5L9.5 8.5L10.5 13L7 10.5L3.5 13L4.5 8.5L1 5.5L5.5 5L7 1Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
          </svg>
          <span className="credit-value">{credits.toLocaleString('tr-TR')}</span>
          <span className="credit-label">analiz</span>
        </Link>

        <div className="user-menu" ref={menuRef}>
          <button className="user-trigger" onClick={() => setMenuOpen(v => !v)} aria-label="Kullanıcı menüsü">
            <div className="avatar">{initial}</div>
          </button>
          {menuOpen && (
            <div className="user-dropdown">
              <div className="user-info">
                <div className="avatar lg">{initial}</div>
                <div>
                  <div className="user-email">{user.email}</div>
                  <div className="user-role">
                    {role === 'admin' && '👑 Admin'}
                    {role === 'agency' && '🏢 Ajans'}
                    {role === 'customer' && '✨ Kullanıcı'}
                  </div>
                </div>
              </div>
              <div className="menu-divider" />
              <Link href="/settings" className="menu-item" onClick={() => setMenuOpen(false)}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.4" /><path d="M8 2V4M8 12V14M2 8H4M12 8H14" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></svg>
                Ayarlar
              </Link>
              <Link href="/credits" className="menu-item" onClick={() => setMenuOpen(false)}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2L9.5 6L14 6.5L10.5 9.5L11.5 14L8 11.5L4.5 14L5.5 9.5L2 6.5L6.5 6L8 2Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /></svg>
                Krediler
              </Link>
              <div className="menu-divider" />
              <button className="menu-item danger" onClick={handleLogout}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6 2H3C2.45 2 2 2.45 2 3V13C2 13.55 2.45 14 3 14H6M11 11L14 8L11 5M14 8H6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" /></svg>
                Çıkış Yap
              </button>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .topbar {
          height: var(--header-h);
          background: var(--surface-1);
          border-bottom: 1px solid var(--border-subtle);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 24px;
          position: sticky;
          top: 0;
          z-index: var(--z-header);
          backdrop-filter: blur(12px);
          background-color: rgba(17, 17, 19, 0.85);
        }
        .topbar-left { display: flex; align-items: center; gap: 12px; }
        .topbar-right { display: flex; align-items: center; gap: 12px; }

        .firm-tag {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          background: var(--surface-2);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-full);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }
        .firm-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--success);
          box-shadow: 0 0 8px var(--success);
        }

        .credit-pill {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border-radius: var(--radius-full);
          background: var(--brand-subtle);
          color: var(--brand-text);
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          transition: all var(--duration-fast) var(--ease-out);
          text-decoration: none;
          border: 1px solid transparent;
        }
        .credit-pill:hover {
          background: rgba(99, 102, 241, 0.18);
          border-color: var(--border-focus);
        }
        .credit-pill.warn {
          background: var(--warning-subtle);
          color: var(--warning-text);
        }
        .credit-value {
          font-variant-numeric: tabular-nums;
          font-weight: var(--weight-bold);
        }
        .credit-label {
          color: var(--text-tertiary);
          font-weight: var(--weight-regular);
          font-size: var(--text-xs);
        }
        .credit-pill.warn .credit-label { color: var(--warning-text); opacity: 0.8; }

        .user-menu {
          position: relative;
        }
        .user-trigger {
          background: none;
          border: none;
          padding: 0;
          cursor: pointer;
          border-radius: 50%;
        }
        .avatar {
          width: 32px;
          height: 32px;
          background: var(--brand-gradient);
          color: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: var(--weight-bold);
          font-size: var(--text-sm);
        }
        .avatar.lg {
          width: 40px;
          height: 40px;
          font-size: var(--text-md);
        }

        .user-dropdown {
          position: absolute;
          right: 0;
          top: calc(100% + 8px);
          min-width: 240px;
          background: var(--surface-2);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-lg);
          box-shadow: var(--shadow-overlay);
          padding: 6px;
          z-index: var(--z-dropdown);
          animation: slideDown var(--duration-fast) var(--ease-out);
        }
        .user-info {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px;
        }
        .user-email {
          font-size: var(--text-sm);
          color: var(--text-primary);
          font-weight: var(--weight-medium);
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 160px;
        }
        .user-role {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .menu-divider {
          height: 1px;
          background: var(--border-subtle);
          margin: 4px 0;
        }
        .menu-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px 10px;
          width: 100%;
          background: none;
          border: none;
          color: var(--text-secondary);
          font-size: var(--text-sm);
          cursor: pointer;
          border-radius: var(--radius-sm);
          text-align: left;
          text-decoration: none;
          font-family: inherit;
        }
        .menu-item:hover {
          background: var(--surface-3);
          color: var(--text-primary);
        }
        .menu-item.danger { color: var(--error-text); }
        .menu-item.danger:hover { background: var(--error-subtle); }
      `}</style>
    </header>
  )
}
