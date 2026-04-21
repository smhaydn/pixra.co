'use client'

import { ButtonHTMLAttributes, forwardRef, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'gradient'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  icon?: ReactNode
  iconRight?: ReactNode
  fullWidth?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading, icon, iconRight, fullWidth, children, className = '', disabled, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={`pbtn pbtn-${variant} pbtn-${size} ${fullWidth ? 'pbtn-full' : ''} ${className}`}
      {...rest}
    >
      {loading ? <span className="pbtn-spinner" aria-hidden /> : icon && <span className="pbtn-icon">{icon}</span>}
      {children && <span className="pbtn-label">{children}</span>}
      {!loading && iconRight && <span className="pbtn-icon">{iconRight}</span>}

      <style jsx>{`
        .pbtn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 0 16px;
          border: 1px solid transparent;
          border-radius: var(--radius-md);
          font-weight: var(--weight-medium);
          cursor: pointer;
          transition: all var(--duration-fast) var(--ease-out);
          white-space: nowrap;
          user-select: none;
          position: relative;
        }
        .pbtn:focus-visible {
          outline: none;
          box-shadow: var(--shadow-focus-ring);
        }
        .pbtn:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        /* Sizes */
        .pbtn-sm { height: 32px; font-size: var(--text-sm); padding: 0 12px; }
        .pbtn-md { height: 38px; font-size: var(--text-base); }
        .pbtn-lg { height: 46px; font-size: var(--text-md); padding: 0 22px; border-radius: var(--radius-lg); }

        .pbtn-full { width: 100%; }

        /* Variants */
        .pbtn-primary {
          background: var(--brand-primary);
          color: #fff;
        }
        .pbtn-primary:hover:not(:disabled) {
          background: var(--brand-hover);
          box-shadow: 0 2px 10px var(--brand-glow);
        }
        .pbtn-primary:active:not(:disabled) { transform: translateY(1px); }

        .pbtn-gradient {
          background: var(--brand-gradient);
          color: #fff;
        }
        .pbtn-gradient:hover:not(:disabled) {
          box-shadow: 0 4px 20px var(--brand-glow);
          transform: translateY(-1px);
        }

        .pbtn-secondary {
          background: var(--surface-3);
          color: var(--text-primary);
          border-color: var(--border-default);
        }
        .pbtn-secondary:hover:not(:disabled) {
          background: var(--surface-4);
          border-color: var(--border-strong);
        }

        .pbtn-ghost {
          background: transparent;
          color: var(--text-secondary);
          border-color: var(--border-default);
        }
        .pbtn-ghost:hover:not(:disabled) {
          background: var(--surface-3);
          color: var(--text-primary);
          border-color: var(--border-strong);
        }

        .pbtn-danger {
          background: transparent;
          color: var(--error-text);
          border-color: rgba(239, 68, 68, 0.2);
        }
        .pbtn-danger:hover:not(:disabled) {
          background: var(--error-subtle);
          border-color: rgba(239, 68, 68, 0.4);
        }

        .pbtn-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .pbtn-label {
          display: inline-block;
        }
        .pbtn-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid currentColor;
          border-right-color: transparent;
          border-radius: 50%;
          animation: spin 0.6s linear infinite;
          opacity: 0.9;
        }
      `}</style>
    </button>
  )
})
