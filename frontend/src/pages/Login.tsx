import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { Alert, Button, Card, Field, Input } from '@/components/ui'
import { ApiError } from '@/lib/api'
import { googleEnabled, requestGoogleAccessToken } from '@/lib/google'
import { useAuth } from '@/lib/auth'

interface LocationState {
  from?: { pathname: string }
}

export function Login() {
  const { user, login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [googleBusy, setGoogleBusy] = useState(false)

  // Dove tornare dopo l'accesso: la pagina che ci ha rimbalzati qui, o la home.
  const destination = (location.state as LocationState | null)?.from?.pathname ?? '/'

  if (user) return <Navigate to={destination} replace />

  const fieldError = (name: string) =>
    error instanceof ApiError ? error.fieldError(name) : undefined

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login(email, password)
      navigate(destination, { replace: true })
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setSubmitting(false)
    }
  }

  const handleGoogle = async () => {
    setGoogleBusy(true)
    setError(null)
    try {
      const token = await requestGoogleAccessToken()
      await loginWithGoogle(token)
      navigate(destination, { replace: true })
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setGoogleBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-bold text-ink-900">Accedi</h1>
      <p className="mt-1 text-sm text-ink-500">
        Entra per partecipare alle discussioni del forum.
      </p>

      <Card className="mt-6 p-6">
        {error && (
          <Alert className="mb-5">
            {error.message}
            {/* Un account bannato riceve un errore generico dal backend: senza
                questa nota l'utente non capirebbe perché le sue credenziali
                corrette non funzionano. */}
            {error instanceof ApiError && error.status === 400 && (
              <span className="mt-1 block text-xs">
                Se le credenziali sono corrette, l'account potrebbe essere sospeso.
              </span>
            )}
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Field label="Email" htmlFor="email" error={fieldError('email')}>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              invalid={Boolean(fieldError('email'))}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nome@esempio.it"
            />
          </Field>

          <Field label="Password" htmlFor="password" error={fieldError('password')}>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              invalid={Boolean(fieldError('password'))}
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>

          <Button type="submit" loading={submitting} className="w-full">
            Accedi
          </Button>
        </form>

        {googleEnabled && (
          <>
            <div className="my-5 flex items-center gap-3">
              <span className="h-px flex-1 bg-slate-200" />
              <span className="text-xs uppercase tracking-wide text-ink-400">
                oppure
              </span>
              <span className="h-px flex-1 bg-slate-200" />
            </div>

            <Button
              variant="secondary"
              className="w-full"
              loading={googleBusy}
              onClick={handleGoogle}
            >
              Continua con Google
            </Button>
          </>
        )}
      </Card>

      <p className="mt-6 text-center text-sm text-ink-500">
        Non hai un account?{' '}
        <Link to="/registrati" className="font-medium text-brand-700 hover:underline">
          Registrati
        </Link>
      </p>
    </div>
  )
}
