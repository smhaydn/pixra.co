'use client'

interface ProgressProps {
  value: number
  max?: number
  label?: string
  showPercent?: boolean
  tone?: 'brand' | 'success' | 'warning'
  size?: 'sm' | 'md'
}

export function Progress({ value, max = 100, label, showPercent, tone = 'brand', size = 'md' }: ProgressProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="prog">
      {(label || showPercent) && (
        <div className="prog-head">
          {label && <span className="prog-label">{label}</span>}
          {showPercent && <span className="prog-percent">{Math.round(percent)}%</span>}
        </div>
      )}
      <div className={`prog-track prog-${size}`}>
        <div className={`prog-fill prog-${tone}`} style={{ width: `${percent}%` }} />
      </div>
      <style jsx>{`
        .prog {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .prog-head {
          display: flex;
          justify-content: space-between;
          font-size: var(--text-xs);
        }
        .prog-label { color: var(--text-secondary); }
        .prog-percent {
          color: var(--text-primary);
          font-weight: var(--weight-semibold);
          font-variant-numeric: tabular-nums;
        }
        .prog-track {
          background: var(--surface-3);
          border-radius: var(--radius-full);
          overflow: hidden;
        }
        .prog-sm { height: 4px; }
        .prog-md { height: 8px; }
        .prog-fill {
          height: 100%;
          border-radius: inherit;
          transition: width var(--duration-slow) var(--ease-out);
        }
        .prog-brand { background: var(--brand-gradient); }
        .prog-success { background: var(--success); }
        .prog-warning { background: var(--warning); }
      `}</style>
    </div>
  )
}
