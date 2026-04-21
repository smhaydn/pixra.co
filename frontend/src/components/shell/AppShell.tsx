'use client'

import { ReactNode } from 'react'
import type { User } from '@supabase/supabase-js'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { ImpersonateBanner, type ImpersonationInfo } from './ImpersonateBanner'
import { ToastProvider } from '@/components/ui/Toast'

export type UserRole = 'customer' | 'agency' | 'admin'

interface AppShellProps {
  user: User
  role?: UserRole
  credits?: number
  firmName?: string
  impersonation?: ImpersonationInfo | null
  children: ReactNode
}

export function AppShell({ user, role = 'customer', credits = 0, firmName, impersonation, children }: AppShellProps) {
  return (
    <ToastProvider>
      <div className="shell">
        <Sidebar role={role} />
        <div className="shell-main">
          {impersonation && <ImpersonateBanner info={impersonation} />}
          <TopBar user={user} role={role} credits={credits} firmName={firmName} />
          <main className="shell-content">{children}</main>
        </div>

        <style jsx>{`
          .shell {
            display: flex;
            min-height: 100vh;
            background: var(--surface-0);
          }
          .shell-main {
            flex: 1;
            margin-left: var(--sidebar-w);
            display: flex;
            flex-direction: column;
            min-width: 0;
          }
          .shell-content {
            flex: 1;
            padding: 28px 36px 64px;
            max-width: var(--content-max);
            width: 100%;
            margin: 0 auto;
          }
          @media (max-width: 900px) {
            .shell-main { margin-left: 0; }
            .shell-content { padding: 20px 16px 48px; }
          }
        `}</style>
      </div>
    </ToastProvider>
  )
}

export function PageHeader({
  title,
  description,
  actions,
  breadcrumb,
}: {
  title: string
  description?: string
  actions?: ReactNode
  breadcrumb?: ReactNode
}) {
  return (
    <div className="pheader">
      {breadcrumb && <div className="pheader-crumb">{breadcrumb}</div>}
      <div className="pheader-row">
        <div>
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
        {actions && <div className="pheader-actions">{actions}</div>}
      </div>

      <style jsx>{`
        .pheader {
          margin-bottom: 28px;
        }
        .pheader-crumb {
          margin-bottom: 12px;
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }
        .pheader-row {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 16px;
          flex-wrap: wrap;
        }
        .pheader h1 {
          margin: 0;
          font-size: var(--text-2xl);
          font-weight: var(--weight-bold);
          letter-spacing: var(--tracking-tight);
        }
        .pheader p {
          margin: 6px 0 0;
          color: var(--text-tertiary);
          font-size: var(--text-sm);
        }
        .pheader-actions {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }
      `}</style>
    </div>
  )
}
