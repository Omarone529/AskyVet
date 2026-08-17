import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Alert, Loading } from './ui'
import { useAuth } from '@/lib/auth'

/**
 * Cancello per le rotte riservate.
 *
 * `adminOnly` distingue i due casi: chi non è loggato viene mandato al login,
 * chi è loggato ma non è amministratore riceve un rifiuto esplicito. Mandare
 * anche il secondo al login sarebbe fuorviante: il problema non è chi è, ma
 * cosa può fare.
 */
export function ProtectedRoute({ adminOnly = false }: { adminOnly?: boolean }) {
  const { user, isAdmin, initialising } = useAuth()
  const location = useLocation()

  // Senza questa attesa, ricaricando una pagina protetta si verrebbe sbattuti
  // al login per un istante prima che il profilo torni dal server.
  if (initialising) return <Loading label="Verifica della sessione…" />

  if (!user) {
    // `state.from` permette di tornare qui dopo l'accesso.
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  if (adminOnly && !isAdmin) {
    return <Alert tone="error">Questa sezione è riservata agli amministratori.</Alert>
  }

  return <Outlet />
}
