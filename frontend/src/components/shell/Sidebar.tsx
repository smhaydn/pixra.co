'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ReactNode } from 'react'

interface NavItem {
  href: string
  label: string
  icon: ReactNode
  badge?: string
  disabled?: boolean
  adminOnly?: boolean
}

const NAV_ITEMS: NavItem[] = [
  {
    href: '/',
    label: 'Dashboard',
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M2.5 9L9 2.5L15.5 9V15.5H11V11.5H7V15.5H2.5V9Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: '/seo',
    label: 'SEO & İçerik',
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M3 3H15V15H3V3Z" stroke="currentColor" strokeWidth="1.4" />
        <path d="M6 7H12M6 10H10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: '/ads',
    label: 'Reklamlar',
    badge: 'Yakında',
    disabled: true,
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M3 8L12 3V15L3 10V8Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
        <path d="M14 7V11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: '/analytics',
    label: 'Analitik',
    badge: 'Yakında',
    disabled: true,
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M3 15V10M8 15V5M13 15V8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: '/credits',
    label: 'Krediler',
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M9 2L11 6.5L15.5 7L12 10.5L13 15L9 12.5L5 15L6 10.5L2.5 7L7 6.5L9 2Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: '/settings',
    label: 'Ayarlar',
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.4" />
        <path d="M9 2V4M9 14V16M2 9H4M14 9H16M4 4L5.5 5.5M12.5 12.5L14 14M4 14L5.5 12.5M12.5 5.5L14 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: '/admin',
    label: 'Admin Panel',
    adminOnly: true,
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M9 2L15 4V9C15 12.5 12 15 9 16C6 15 3 12.5 3 9V4L9 2Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
      </svg>
    ),
  },
]

interface SidebarProps {
  role: 'customer' | 'agency' | 'admin'
}

export function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname()

  const visibleItems = NAV_ITEMS.filter(item => !item.adminOnly || role === 'admin')

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" aria-hidden>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M3 13L8 3L13 13H3Z" fill="white" />
          </svg>
        </div>
        <span className="brand-text">Pixra</span>
        <span className="brand-suffix">AI</span>
      </div>

      <nav className="nav" aria-label="Ana gezinti">
        {visibleItems.map(item => {
          const isActive = item.href === '/' ? pathname === '/' : pathname?.startsWith(item.href)
          const Wrapper = item.disabled ? 'span' : Link
          return (
            <Wrapper
              key={item.href}
              href={item.href}
              className={`nav-link ${isActive ? 'active' : ''} ${item.disabled ? 'disabled' : ''} ${item.adminOnly ? 'admin' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </Wrapper>
          )
        })}
      </nav>

      <div className="hint">
        <div className="hint-icon">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.4" />
            <path d="M7 4.5V7.5M7 9.5V9.6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
        </div>
        <p>Yardıma mı ihtiyacın var? <br /><a href="https://wa.me/905000000000" target="_blank" rel="noopener">WhatsApp Destek</a></p>
      </div>

      <style jsx>{`
        .sidebar {
          width: var(--sidebar-w);
          background: var(--surface-1);
          border-right: 1px solid var(--border-subtle);
          display: flex;
          flex-direction: column;
          padding: 18px 12px;
          position: fixed;
          inset: 0 auto 0 0;
          z-index: var(--z-sidebar);
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 0 10px 20px;
          margin-bottom: 12px;
          border-bottom: 1px solid var(--border-subtle);
        }
        .brand-mark {
          width: 30px;
          height: 30px;
          background: var(--brand-gradient);
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 8px var(--brand-glow);
        }
        .brand-text {
          font-size: var(--text-lg);
          font-weight: var(--weight-bold);
          letter-spacing: var(--tracking-tight);
        }
        .brand-suffix {
          font-size: 0.68rem;
          font-weight: var(--weight-semibold);
          color: var(--brand-text);
          background: var(--brand-subtle);
          padding: 2px 7px;
          border-radius: var(--radius-sm);
          letter-spacing: 0.5px;
          margin-left: auto;
        }

        .nav {
          display: flex;
          flex-direction: column;
          gap: 2px;
          flex: 1;
        }
        .nav-link {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 9px 10px;
          border-radius: var(--radius-md);
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          transition: all var(--duration-fast) var(--ease-out);
          cursor: pointer;
          text-decoration: none;
        }
        .nav-link:not(.disabled):hover {
          background: var(--surface-3);
          color: var(--text-primary);
        }
        .nav-link.active {
          background: var(--brand-subtle);
          color: var(--brand-text);
        }
        .nav-link.active .nav-icon {
          color: var(--brand-primary);
        }
        .nav-link.disabled {
          opacity: 0.45;
          cursor: default;
        }
        .nav-link.admin {
          color: var(--warning-text);
        }
        .nav-link.admin.active {
          background: var(--warning-subtle);
          color: var(--warning);
        }
        .nav-icon {
          display: inline-flex;
          width: 18px;
          height: 18px;
          flex-shrink: 0;
        }
        .nav-label { flex: 1; }
        .nav-badge {
          font-size: 0.6rem;
          padding: 2px 6px;
          border-radius: var(--radius-sm);
          background: var(--surface-4);
          color: var(--text-muted);
          font-weight: var(--weight-medium);
          letter-spacing: 0.3px;
        }

        .hint {
          display: flex;
          gap: 10px;
          padding: 14px;
          background: var(--surface-2);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          line-height: 1.45;
        }
        .hint-icon {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: var(--brand-subtle);
          color: var(--brand-text);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .hint p { margin: 0; }
        .hint a {
          color: var(--brand-text);
          font-weight: var(--weight-semibold);
          text-decoration: none;
        }
        .hint a:hover { text-decoration: underline; }

        @media (max-width: 900px) {
          .sidebar {
            transform: translateX(-100%);
            transition: transform var(--duration-base) var(--ease-out);
          }
        }
      `}</style>
    </aside>
  )
}
