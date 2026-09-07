import { cloneElement, isValidElement, useId } from 'react'
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

import { mediaUrl } from '@/lib/api'
import { initials } from '@/lib/format'

/** Concatena classi ignorando i valori falsy. */
export function cx(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ')
}

// -------------------------------------------------------------------- Button

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 disabled:hover:bg-brand-600',
  secondary:
    'bg-white text-ink-900 ring-1 ring-slate-300 hover:bg-slate-50 disabled:hover:bg-white',
  ghost: 'text-ink-700 hover:bg-slate-100 disabled:hover:bg-transparent',
  danger: 'bg-red-600 text-white hover:bg-red-700 disabled:hover:bg-red-600',
}

const SIZES: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      // Il default di <button> dentro un form è "submit": senza type esplicito
      // un pulsante secondario invierebbe il form per sbaglio.
      type={type}
      disabled={disabled || loading}
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-60',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  )
}

// --------------------------------------------------------------------- Campi

interface FieldProps {
  label: string
  error?: string | undefined
  hint?: string
  children: ReactNode
  htmlFor?: string
}

export function Field({ label, error, hint, children, htmlFor }: FieldProps) {
  const generatedId = useId()

  // L'etichetta va collegata al controllo, altrimenti uno screen reader legge
  // un campo senza nome. Se il chiamante non passa htmlFor/id, l'id viene
  // generato e iniettato qui: così l'associazione non può essere dimenticata.
  const child = children
  const needsInjection =
    !htmlFor && isValidElement<{ id?: string }>(child) && !child.props.id

  const controlId = htmlFor ?? (needsInjection ? generatedId : undefined)

  return (
    <div className="space-y-1.5">
      <label htmlFor={controlId} className="block text-sm font-medium text-ink-900">
        {label}
      </label>

      {needsInjection && isValidElement<{ id?: string }>(child)
        ? cloneElement(child, { id: generatedId })
        : child}

      {hint && !error && <p className="text-xs text-ink-500">{hint}</p>}
      {/* role="alert" fa annunciare l'errore agli screen reader appena compare. */}
      {error && (
        <p role="alert" className="text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}

const CONTROL =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-ink-900 ' +
  'placeholder:text-ink-400 focus:border-brand-500 focus:outline-none ' +
  'disabled:bg-slate-100 disabled:text-ink-500'

export function Input({
  className,
  invalid,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cx(CONTROL, invalid && 'border-red-400', className)}
      {...props}
    />
  )
}

export function Textarea({
  className,
  invalid,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }) {
  return (
    <textarea
      aria-invalid={invalid || undefined}
      className={cx(CONTROL, 'resize-y', invalid && 'border-red-400', className)}
      {...props}
    />
  )
}

export function Select({
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cx(CONTROL, 'pr-8', className)} {...props} />
}

// ------------------------------------------------------------------ Feedback

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cx('animate-spin text-current', className ?? 'h-5 w-5')}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  )
}

/**
 * Sagoma grigia che pulsa al posto del contenuto non ancora arrivato.
 *
 * Neutra di proposito: nessun testo, nessuna animazione a tema, niente che
 * spieghi cosa sta succedendo dietro. È lo stesso pattern che usano tutti i
 * siti moderni anche con il backend ben sveglio, quindi comunica "sto
 * caricando" e nient'altro — in particolare non lascia intuire che c'è un
 * servizio che si stava risvegliando.
 */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cx('animate-pulse rounded bg-slate-200', className)}
      aria-hidden="true"
    />
  )
}

export function Loading({ label = 'Caricamento…' }: { label?: string }) {
  return (
    <div
      role="status"
      className="flex items-center justify-center gap-3 py-16 text-ink-500"
    >
      <Spinner />
      <span className="text-sm">{label}</span>
    </div>
  )
}

type AlertTone = 'error' | 'success' | 'info' | 'warning'

const TONES: Record<AlertTone, string> = {
  error: 'bg-red-50 text-red-800 ring-red-200',
  success: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  info: 'bg-brand-50 text-brand-900 ring-brand-200',
  warning: 'bg-amber-50 text-amber-900 ring-amber-200',
}

export function Alert({
  tone = 'error',
  children,
  className,
}: {
  tone?: AlertTone
  children: ReactNode
  className?: string
}) {
  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={cx('rounded-lg px-4 py-3 text-sm ring-1', TONES[tone], className)}
    >
      {children}
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white/60 px-6 py-14 text-center">
      <p className="font-medium text-ink-900">{title}</p>
      {description && <p className="mt-1 text-sm text-ink-500">{description}</p>}
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  )
}

// ----------------------------------------------------------------- Contenuti

export function Card({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div
      className={cx('rounded-xl border border-slate-200 bg-white shadow-sm', className)}
    >
      {children}
    </div>
  )
}

type BadgeTone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger'

const BADGE_TONES: Record<BadgeTone, string> = {
  neutral: 'bg-slate-100 text-ink-700',
  brand: 'bg-brand-100 text-brand-900',
  success: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-900',
  danger: 'bg-red-100 text-red-800',
}

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: BadgeTone
  children: ReactNode
}) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        BADGE_TONES[tone],
      )}
    >
      {children}
    </span>
  )
}

export function Avatar({
  username,
  src,
  size = 36,
}: {
  username: string
  src?: string | null
  size?: number
}) {
  const url = mediaUrl(src ?? null)

  if (url) {
    return (
      <img
        src={url}
        alt=""
        className="shrink-0 rounded-full object-cover"
        style={{ width: size, height: size }}
      />
    )
  }

  return (
    <span
      aria-hidden="true"
      className="inline-flex shrink-0 items-center justify-center rounded-full bg-brand-100 font-semibold text-brand-900"
      style={{ width: size, height: size, fontSize: size * 0.36 }}
    >
      {initials(username)}
    </span>
  )
}

// --------------------------------------------------------------- Paginazione

export function Pagination({
  page,
  count,
  pageSize = 20,
  onChange,
}: {
  page: number
  count: number
  pageSize?: number
  onChange: (page: number) => void
}) {
  const pages = Math.ceil(count / pageSize)
  if (pages <= 1) return null

  return (
    <nav
      aria-label="Paginazione"
      className="flex items-center justify-center gap-3 pt-8"
    >
      <Button
        variant="secondary"
        size="sm"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        Precedente
      </Button>
      <span className="text-sm text-ink-500" aria-live="polite">
        Pagina {page} di {pages}
      </span>
      <Button
        variant="secondary"
        size="sm"
        disabled={page >= pages}
        onClick={() => onChange(page + 1)}
      >
        Successiva
      </Button>
    </nav>
  )
}
