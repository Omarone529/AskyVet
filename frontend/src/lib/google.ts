/**
 * Accesso con Google, lato browser.
 *
 * Usa Google Identity Services per ottenere un access token, che viene poi
 * inviato a /api/auth/google/: è il backend a farlo verificare da Google e a
 * restituire la coppia JWT dell'applicazione.
 */

const GIS_SRC = 'https://accounts.google.com/gsi/client'

export const GOOGLE_CLIENT_ID: string = import.meta.env['VITE_GOOGLE_CLIENT_ID'] ?? ''

/** Il pulsante Google va nascosto del tutto se il client id non è configurato. */
export const googleEnabled = Boolean(GOOGLE_CLIENT_ID)

interface TokenResponse {
  access_token?: string
  error?: string
}

interface TokenClient {
  requestAccessToken: () => void
}

interface GoogleOAuth2 {
  initTokenClient: (config: {
    client_id: string
    scope: string
    callback: (response: TokenResponse) => void
    error_callback?: (error: { type?: string }) => void
  }) => TokenClient
}

declare global {
  interface Window {
    google?: { accounts: { oauth2: GoogleOAuth2 } }
  }
}

let scriptPromise: Promise<void> | null = null

/** Carica lo script una sola volta, anche se due pagine lo chiedono insieme. */
function loadScript(): Promise<void> {
  if (window.google?.accounts?.oauth2) return Promise.resolve()

  scriptPromise ??= new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = GIS_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => {
      // Rimosso dalla cache: un errore di rete non deve impedire un secondo
      // tentativo dopo che la connessione è tornata.
      scriptPromise = null
      reject(new Error('Impossibile caricare Google Identity Services.'))
    }
    document.head.appendChild(script)
  })

  return scriptPromise
}

/**
 * Apre il popup di Google e risolve con l'access token.
 *
 * Rifiuta se l'utente chiude il popup o nega il consenso: chi chiama deve
 * distinguere l'annullamento da un errore vero.
 */
export async function requestGoogleAccessToken(): Promise<string> {
  if (!googleEnabled) {
    throw new Error('Accesso con Google non configurato (VITE_GOOGLE_CLIENT_ID).')
  }

  await loadScript()

  const oauth2 = window.google?.accounts?.oauth2
  if (!oauth2) throw new Error('Google Identity Services non disponibile.')

  return new Promise<string>((resolve, reject) => {
    const client = oauth2.initTokenClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: 'openid email profile',
      callback: (response) => {
        if (response.access_token) resolve(response.access_token)
        else reject(new Error(response.error ?? 'Accesso con Google annullato.'))
      },
      error_callback: () => reject(new Error('Accesso con Google annullato.')),
    })

    client.requestAccessToken()
  })
}
