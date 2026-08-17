import type { AuthTokens } from '@/types'

const BASE_URL = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8000'

const ACCESS_KEY = 'askyvet.access'
const REFRESH_KEY = 'askyvet.refresh'

/** Errore che porta con sé lo stato HTTP e gli errori di campo di DRF. */
export class ApiError extends Error {
  status: number
  /** Errori per campo, es. { email: ["Esiste già un utente con questa email."] } */
  fields: Record<string, string[]>

  constructor(
    status: number,
    message: string,
    fields: Record<string, string[]> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fields = fields
  }

  /** Messaggio pronto da mostrare per un campo specifico. */
  fieldError(name: string): string | undefined {
    return this.fields[name]?.[0]
  }
}

// --------------------------------------------------------------------- Token

export const tokens = {
  access: () => localStorage.getItem(ACCESS_KEY),
  refresh: () => localStorage.getItem(REFRESH_KEY),

  save(next: AuthTokens) {
    localStorage.setItem(ACCESS_KEY, next.access)
    localStorage.setItem(REFRESH_KEY, next.refresh)
  },

  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

/** Notifica l'AuthProvider quando la sessione decade, per svuotare lo stato. */
type SessionExpiredHandler = () => void
let onSessionExpired: SessionExpiredHandler = () => {}

export function setSessionExpiredHandler(handler: SessionExpiredHandler) {
  onSessionExpired = handler
}

// ------------------------------------------------------------------- Rinnovo

/**
 * Rinnovo in corso, condiviso fra tutte le richieste.
 *
 * Se tre chiamate scadono insieme, senza questa promessa partirebbero tre
 * refresh: il backend ruota i token e mette in blacklist il precedente, quindi
 * il primo invaliderebbe gli altri due e l'utente verrebbe buttato fuori.
 */
let refreshInFlight: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refresh = tokens.refresh()
  if (!refresh) throw new ApiError(401, 'Sessione scaduta.')

  const response = await fetch(`${BASE_URL}/api/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })

  if (!response.ok) {
    tokens.clear()
    onSessionExpired()
    throw new ApiError(401, 'Sessione scaduta, effettua di nuovo l’accesso.')
  }

  const data = (await response.json()) as { access: string; refresh?: string }

  // ROTATE_REFRESH_TOKENS è attivo lato Django: quando arriva un refresh nuovo
  // il vecchio è già in blacklist e va sostituito, altrimenti il rinnovo
  // successivo fallisce.
  tokens.save({ access: data.access, refresh: data.refresh ?? refresh })

  return data.access
}

// ----------------------------------------------------------------- Richieste

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  /** Serializzato in JSON, oppure passato così com'è se è un FormData. */
  body?: unknown
  params?: Record<string, string | number | undefined | null>
  /** Salta il rinnovo automatico (usato dal login stesso). */
  skipAuth?: boolean
}

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const url = new URL(path.startsWith('http') ? path : `${BASE_URL}${path}`)
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

async function toApiError(response: Response): Promise<ApiError> {
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    return new ApiError(response.status, `Errore ${response.status}.`)
  }

  if (typeof payload !== 'object' || payload === null) {
    return new ApiError(response.status, `Errore ${response.status}.`)
  }

  const data = payload as Record<string, unknown>

  // DRF risponde con {"detail": "..."} oppure {"campo": ["errore", ...]}.
  const detail = typeof data['detail'] === 'string' ? data['detail'] : undefined

  const fields: Record<string, string[]> = {}
  for (const [key, value] of Object.entries(data)) {
    if (key === 'detail') continue
    if (Array.isArray(value)) fields[key] = value.map(String)
    else if (typeof value === 'string') fields[key] = [value]
  }

  const firstField = Object.values(fields)[0]?.[0]
  const message =
    detail ?? firstField ?? `Errore ${response.status}. Riprova più tardi.`

  return new ApiError(response.status, message, fields)
}

async function send(
  path: string,
  options: RequestOptions,
  accessToken: string | null,
) {
  const isFormData = options.body instanceof FormData
  const headers: Record<string, string> = {}

  // Con FormData il Content-Type lo imposta il browser, boundary incluso:
  // scriverlo a mano romperebbe l'upload della copertina.
  if (!isFormData && options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  return fetch(buildUrl(path, options.params), {
    method: options.method ?? 'GET',
    headers,
    body: isFormData
      ? (options.body as FormData)
      : options.body !== undefined
        ? JSON.stringify(options.body)
        : undefined,
  })
}

/**
 * Esegue una richiesta verso l'API.
 *
 * Su 401 con un refresh disponibile rinnova il token una sola volta e ritenta.
 * Un secondo 401 significa che la sessione è davvero finita.
 */
export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  let response = await send(
    path,
    options,
    options.skipAuth ? null : tokens.access(),
  )

  if (response.status === 401 && !options.skipAuth && tokens.refresh()) {
    try {
      refreshInFlight ??= refreshAccessToken().finally(() => {
        refreshInFlight = null
      })
      const fresh = await refreshInFlight
      response = await send(path, options, fresh)
    } catch (error) {
      tokens.clear()
      onSessionExpired()
      throw error
    }
  }

  if (!response.ok) throw await toApiError(response)

  // 204 sulle DELETE: nessun corpo da interpretare.
  if (response.status === 204) return undefined as T

  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string, params?: RequestOptions['params']) =>
    request<T>(path, params ? { params } : {}),
  post: <T>(path: string, body?: unknown, opts?: Pick<RequestOptions, 'skipAuth'>) =>
    request<T>(path, { method: 'POST', body, ...opts }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

/** Rende assoluto un percorso media restituito dall'API. */
export function mediaUrl(path: string | null): string | null {
  if (!path) return null
  return path.startsWith('http') ? path : `${BASE_URL}${path}`
}
