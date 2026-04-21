'use client'

import { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="empty">
      {icon && <div className="empty-icon">{icon}</div>}
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action && <div className="empty-action">{action}</div>}

      <style jsx>{`
        .empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 48px 24px;
          background: var(--surface-1);
          border: 1px dashed var(--border-default);
          border-radius: var(--radius-lg);
        }
        .empty-icon {
          width: 56px;
          height: 56px;
          border-radius: var(--radius-xl);
          background: var(--brand-subtle);
          color: var(--brand-text);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 16px;
        }
        .empty h3 {
          margin: 0 0 6px;
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
        }
        .empty p {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          max-width: 360px;
          margin: 0;
        }
        .empty-action {
          margin-top: 20px;
        }
      `}</style>
    </div>
  )
}
