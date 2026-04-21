'use client'

import { ReactNode, useEffect } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  description?: string
  children: ReactNode
  footer?: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

export function Modal({ open, onClose, title, description, children, footer, size = 'md' }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEsc)
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = originalOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className={`modal modal-${size}`} onClick={e => e.stopPropagation()}>
        {(title || description) && (
          <div className="modal-head">
            <div>
              {title && <h3>{title}</h3>}
              {description && <p>{description}</p>}
            </div>
            <button className="modal-x" onClick={onClose} aria-label="Kapat">×</button>
          </div>
        )}
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
      <style jsx>{`
        .modal-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.65);
          backdrop-filter: blur(6px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: var(--z-modal);
          padding: 16px;
          animation: fadeIn var(--duration-fast) var(--ease-out);
        }
        .modal {
          width: 100%;
          background: var(--surface-2);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-xl);
          box-shadow: var(--shadow-overlay);
          animation: slideUp var(--duration-base) var(--ease-out);
          display: flex;
          flex-direction: column;
          max-height: 90vh;
          overflow: hidden;
        }
        .modal-sm { max-width: 400px; }
        .modal-md { max-width: 520px; }
        .modal-lg { max-width: 720px; }

        .modal-head {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 20px 24px 12px;
          gap: 16px;
        }
        .modal-head h3 {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          margin: 0;
        }
        .modal-head p {
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          margin: 4px 0 0;
        }
        .modal-x {
          background: none;
          border: none;
          color: var(--text-muted);
          font-size: 1.5rem;
          cursor: pointer;
          line-height: 1;
          padding: 0 4px;
        }
        .modal-x:hover { color: var(--text-primary); }

        .modal-body {
          padding: 8px 24px 20px;
          overflow-y: auto;
          flex: 1;
        }
        .modal-foot {
          display: flex;
          justify-content: flex-end;
          gap: 8px;
          padding: 16px 24px;
          border-top: 1px solid var(--border-subtle);
          background: var(--surface-1);
        }
      `}</style>
    </div>
  )
}
