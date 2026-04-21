'use client'

import { CSSProperties, ReactNode } from 'react'

type Tone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger' | 'info'

interface BadgeProps {
  children: ReactNode
  tone?: Tone
  dot?: boolean
  soft?: boolean
  style?: CSSProperties
}

export function Badge({ children, tone = 'neutral', dot, soft = true, style }: BadgeProps) {
  return (
    <span className={`pbadge pbadge-${tone} ${soft ? 'soft' : 'solid'}`} style={style}>
      {dot && <span className="pbadge-dot" aria-hidden />}
      {children}
      <style jsx>{`
        .pbadge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
          padding: 3px 8px;
          border-radius: var(--radius-sm);
          line-height: 1.4;
          border: 1px solid transparent;
          white-space: nowrap;
        }
        .pbadge-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: currentColor;
          flex-shrink: 0;
        }

        /* Soft variants */
        .soft.pbadge-neutral {
          background: var(--surface-3);
          color: var(--text-tertiary);
        }
        .soft.pbadge-brand {
          background: var(--brand-subtle);
          color: var(--brand-text);
        }
        .soft.pbadge-success {
          background: var(--success-subtle);
          color: var(--success-text);
        }
        .soft.pbadge-warning {
          background: var(--warning-subtle);
          color: var(--warning-text);
        }
        .soft.pbadge-danger {
          background: var(--error-subtle);
          color: var(--error-text);
        }
        .soft.pbadge-info {
          background: var(--info-subtle);
          color: var(--info-text);
        }

        /* Solid variants */
        .solid.pbadge-neutral { background: var(--surface-4); color: var(--text-primary); }
        .solid.pbadge-brand { background: var(--brand-primary); color: #fff; }
        .solid.pbadge-success { background: var(--success); color: #04130a; }
        .solid.pbadge-warning { background: var(--warning); color: #1a1000; }
        .solid.pbadge-danger { background: var(--error); color: #fff; }
        .solid.pbadge-info { background: var(--info); color: #fff; }
      `}</style>
    </span>
  )
}
