'use client'

import { createContext, useContext, useState, useCallback, useRef, ReactNode } from 'react'

type ToastType = 'success' | 'error' | 'info' | 'warning'
interface ToastItem { id: number; message: string; type: ToastType }

interface ToastContextValue {
  show: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const idRef = useRef(0)

  const show = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++idRef.current
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }, [])

  const remove = (id: number) => setToasts(prev => prev.filter(t => t.id !== id))

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            <span className="toast-icon">
              {t.type === 'success' && '✓'}
              {t.type === 'error' && '!'}
              {t.type === 'warning' && '⚠'}
              {t.type === 'info' && 'i'}
            </span>
            <span className="toast-text">{t.message}</span>
            <button className="toast-close" onClick={() => remove(t.id)} aria-label="Kapat">×</button>
          </div>
        ))}
      </div>
      <style jsx>{`
        .toast-stack {
          position: fixed;
          top: 16px;
          right: 16px;
          z-index: var(--z-toast);
          display: flex;
          flex-direction: column;
          gap: 8px;
          pointer-events: none;
        }
        .toast {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 14px;
          background: var(--surface-3);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-md);
          box-shadow: var(--shadow-lg);
          max-width: 360px;
          font-size: var(--text-sm);
          pointer-events: auto;
          animation: slideIn var(--duration-slow) var(--ease-out);
        }
        .toast-success { border-left: 3px solid var(--success); }
        .toast-error { border-left: 3px solid var(--error); }
        .toast-warning { border-left: 3px solid var(--warning); }
        .toast-info { border-left: 3px solid var(--info); }

        .toast-icon {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.72rem;
          font-weight: 700;
          flex-shrink: 0;
        }
        .toast-success .toast-icon { background: var(--success-subtle); color: var(--success-text); }
        .toast-error .toast-icon { background: var(--error-subtle); color: var(--error-text); }
        .toast-warning .toast-icon { background: var(--warning-subtle); color: var(--warning-text); }
        .toast-info .toast-icon { background: var(--info-subtle); color: var(--info-text); }

        .toast-text {
          flex: 1;
          color: var(--text-primary);
          line-height: 1.4;
        }
        .toast-close {
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          font-size: 1.1rem;
          padding: 0 4px;
          line-height: 1;
        }
        .toast-close:hover { color: var(--text-primary); }
      `}</style>
    </ToastContext.Provider>
  )
}
