const dateFormatter = new Intl.DateTimeFormat('it-IT', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

const dateTimeFormatter = new Intl.DateTimeFormat('it-IT', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const relativeFormatter = new Intl.RelativeTimeFormat('it-IT', { numeric: 'auto' })

/** "14 marzo 2026" */
export function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return dateFormatter.format(new Date(iso))
}

/** "14/03/2026, 18:20" */
export function formatDateTime(iso: string | null): string {
  if (!iso) return '—'
  return dateTimeFormatter.format(new Date(iso))
}

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 60 * 60],
  ['month', 30 * 24 * 60 * 60],
  ['day', 24 * 60 * 60],
  ['hour', 60 * 60],
  ['minute', 60],
]

/**
 * "3 ore fa", "ieri", "2 mesi fa".
 *
 * Oltre l'anno passa alla data assoluta: "1 anno fa" su un contenuto di tre
 * anni è più fuorviante che utile.
 */
export function formatRelative(iso: string | null): string {
  if (!iso) return '—'

  const seconds = (Date.now() - new Date(iso).getTime()) / 1000
  if (seconds < 45) return 'poco fa'
  if (seconds > 365 * 24 * 60 * 60) return formatDate(iso)

  for (const [unit, unitSeconds] of UNITS) {
    if (seconds >= unitSeconds) {
      return relativeFormatter.format(-Math.floor(seconds / unitSeconds), unit)
    }
  }
  return 'poco fa'
}

/** Taglia sull'ultimo spazio utile, così non si spezzano le parole. */
export function truncate(text: string, max = 160): string {
  if (text.length <= max) return text
  const cut = text.slice(0, max)
  const lastSpace = cut.lastIndexOf(' ')
  return `${cut.slice(0, lastSpace > 0 ? lastSpace : max).trimEnd()}…`
}

/** Iniziali per l'avatar segnaposto di un utente senza immagine. */
export function initials(username: string): string {
  return username.slice(0, 2).toUpperCase()
}
