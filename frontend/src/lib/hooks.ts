import { useCallback, useEffect, useRef, useState } from 'react'

import { ApiError } from './api'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

/**
 * Carica dati dall'API e ne espone stato e messaggio d'errore.
 *
 * `deps` funziona come per useEffect: quando cambia, ricarica. Il risultato di
 * una richiesta ormai superata viene scartato, così tornando indietro in fretta
 * fra due pagine non si vedono i dati della precedente comparire su quella
 * nuova.
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: readonly unknown[] = [],
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  })
  const [nonce, setNonce] = useState(0)

  // In un ref, non fra le deps: una funzione inline cambierebbe a ogni render
  // e l'effetto girerebbe all'infinito.
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const key = JSON.stringify(deps)

  useEffect(() => {
    let active = true
    setState((prev) => ({ ...prev, loading: true, error: null }))

    fetcherRef
      .current()
      .then((data) => {
        if (active) setState({ data, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (!active) return
        setState({
          data: null,
          loading: false,
          error:
            error instanceof ApiError
              ? error.message
              : 'Impossibile contattare il server. Verifica che il backend sia avviato.',
        })
      })

    return () => {
      active = false
    }
  }, [key, nonce])

  const reload = useCallback(() => setNonce((n) => n + 1), [])

  return { ...state, reload }
}

/** Ritarda un valore: evita una chiamata all'API a ogni tasto premuto. */
export function useDebounced<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
