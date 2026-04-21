'use client'

import { useTransition } from 'react'
import { exitImpersonate } from '@/app/admin/customers/actions'

export interface ImpersonationInfo {
  adminEmail: string | null
  targetEmail: string | null
}

export function ImpersonateBanner({ info }: { info: ImpersonationInfo }) {
  const [pending, start] = useTransition()

  return (
    <div className="imp-banner">
      <div className="imp-inner">
        <span className="imp-mask">🎭</span>
        <span className="imp-msg">
          <strong>{info.targetEmail || 'Müşteri'}</strong> olarak görüntülüyorsun
          {info.adminEmail && <span className="imp-admin"> · Admin: {info.adminEmail}</span>}
        </span>
        <button
          className="imp-exit"
          disabled={pending}
          onClick={() => start(() => exitImpersonate())}
        >
          {pending ? 'Çıkılıyor…' : 'Impersonate\'ten çık'}
        </button>
      </div>

      <style jsx>{`
        .imp-banner {
          position: sticky;
          top: 0;
          z-index: var(--z-header);
          background: linear-gradient(90deg, #f59e0b 0%, #ef4444 100%);
          color: white;
          font-size: var(--text-sm);
          box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
        }
        .imp-inner {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 20px;
          max-width: var(--content-max);
          margin: 0 auto;
        }
        .imp-mask { font-size: 1.1rem; }
        .imp-msg { flex: 1; }
        .imp-admin {
          opacity: 0.85;
          font-size: var(--text-xs);
          margin-left: 4px;
        }
        .imp-exit {
          background: rgba(0, 0, 0, 0.25);
          border: 1px solid rgba(255, 255, 255, 0.3);
          color: white;
          padding: 6px 14px;
          border-radius: var(--radius-sm);
          font-size: var(--text-xs);
          font-weight: var(--weight-semibold);
          cursor: pointer;
          transition: background var(--duration-fast) var(--ease-out);
        }
        .imp-exit:hover:not(:disabled) { background: rgba(0, 0, 0, 0.4); }
        .imp-exit:disabled { opacity: 0.6; cursor: not-allowed; }
      `}</style>
    </div>
  )
}
