'use client'

import { InputHTMLAttributes, forwardRef, ReactNode } from 'react'

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  label?: string
  hint?: string
  error?: string
  prefix?: ReactNode
  suffix?: ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, prefix, suffix, id, className = '', ...rest },
  ref,
) {
  const inputId = id || `inp-${Math.random().toString(36).slice(2, 8)}`
  return (
    <div className={`pinput-wrap ${className}`}>
      {label && (
        <label htmlFor={inputId} className="pinput-label">
          {label}
          {rest.required && <span className="pinput-req">*</span>}
        </label>
      )}
      <div className={`pinput-field ${error ? 'has-error' : ''}`}>
        {prefix && <span className="pinput-prefix">{prefix}</span>}
        <input ref={ref} id={inputId} {...rest} />
        {suffix && <span className="pinput-suffix">{suffix}</span>}
      </div>
      {error ? (
        <span className="pinput-error">{error}</span>
      ) : hint ? (
        <span className="pinput-hint">{hint}</span>
      ) : null}

      <style jsx>{`
        .pinput-wrap {
          display: flex;
          flex-direction: column;
          gap: 6px;
          width: 100%;
        }
        .pinput-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-secondary);
        }
        .pinput-req {
          color: var(--error-text);
          margin-left: 2px;
        }
        .pinput-field {
          display: flex;
          align-items: center;
          gap: 8px;
          border: 1px solid var(--border-default);
          background: var(--surface-2);
          border-radius: var(--radius-md);
          transition: border-color var(--duration-fast) var(--ease-out),
                      box-shadow var(--duration-fast) var(--ease-out);
          padding: 0 12px;
        }
        .pinput-field:focus-within {
          border-color: var(--brand-primary);
          box-shadow: var(--shadow-focus-ring);
        }
        .pinput-field.has-error {
          border-color: var(--error);
        }
        .pinput-field.has-error:focus-within {
          box-shadow: 0 0 0 3px var(--error-subtle);
        }
        .pinput-field :global(input) {
          flex: 1;
          height: 38px;
          border: none;
          background: transparent;
          color: var(--text-primary);
          font-size: var(--text-base);
          outline: none;
          min-width: 0;
          padding: 0;
          font-family: inherit;
        }
        .pinput-field :global(input::placeholder) {
          color: var(--text-muted);
        }
        .pinput-prefix, .pinput-suffix {
          color: var(--text-tertiary);
          display: inline-flex;
          align-items: center;
          flex-shrink: 0;
        }
        .pinput-hint {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }
        .pinput-error {
          font-size: var(--text-xs);
          color: var(--error-text);
        }
      `}</style>
    </div>
  )
})
