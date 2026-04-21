'use client'

import { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  variant?: 'default' | 'elevated' | 'magic' | 'flat'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  interactive?: boolean
}

export function Card({ children, variant = 'default', padding = 'md', interactive, className = '', ...rest }: CardProps) {
  return (
    <div
      className={`pcard pcard-${variant} pcard-p-${padding} ${interactive ? 'pcard-interactive' : ''} ${className}`}
      {...rest}
    >
      {children}
      <style jsx>{`
        .pcard {
          border-radius: var(--radius-lg);
          border: 1px solid var(--border-subtle);
          background: var(--surface-1);
          transition: border-color var(--duration-fast) var(--ease-out),
                      transform var(--duration-base) var(--ease-out),
                      box-shadow var(--duration-base) var(--ease-out);
        }
        .pcard-elevated {
          background: var(--surface-2);
          border-color: var(--border-default);
          box-shadow: var(--shadow-sm);
        }
        .pcard-flat {
          background: transparent;
          border-color: var(--border-subtle);
        }
        .pcard-magic {
          background: var(--magic-bg), var(--surface-1);
          background-blend-mode: normal;
          border: 1px solid transparent;
          background-clip: padding-box;
          position: relative;
        }
        .pcard-magic::before {
          content: '';
          position: absolute;
          inset: -1px;
          padding: 1px;
          border-radius: inherit;
          background: var(--magic-border);
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
          -webkit-mask-composite: xor;
          mask-composite: exclude;
          pointer-events: none;
          opacity: 0.6;
        }

        .pcard-p-none { padding: 0; }
        .pcard-p-sm { padding: 12px 14px; }
        .pcard-p-md { padding: 18px 20px; }
        .pcard-p-lg { padding: 24px 28px; }

        .pcard-interactive { cursor: pointer; }
        .pcard-interactive:hover {
          border-color: var(--border-strong);
          transform: translateY(-1px);
          box-shadow: var(--shadow-md);
        }
      `}</style>
    </div>
  )
}

export function CardHeader({ children, actions }: { children: ReactNode; actions?: ReactNode }) {
  return (
    <div className="pcard-header">
      <div className="pcard-header-content">{children}</div>
      {actions && <div className="pcard-header-actions">{actions}</div>}
      <style jsx>{`
        .pcard-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 14px;
        }
        .pcard-header-content :global(h3),
        .pcard-header-content :global(h2) {
          margin: 0;
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          line-height: var(--leading-tight);
        }
        .pcard-header-content :global(p) {
          margin-top: 4px;
          color: var(--text-tertiary);
          font-size: var(--text-sm);
        }
        .pcard-header-actions {
          flex-shrink: 0;
        }
      `}</style>
    </div>
  )
}
