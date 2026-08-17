import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { Alert, Button, Card, Field, Input } from '@/components/ui'
import { ApiError } from '@/lib/api'
import { googleEnabled, requestGoogleAccessToken } from '@/lib/google'
import { useAuth } from '@/lib/auth'

export function Register() {
  const { user, register, loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [googleBusy, setGoogleBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const update = (field: keyof typeof form, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  const fieldError = (name: string) =>
    error instanceof ApiError ? error.fieldError(name) : undefined

  // Controllato qui e non solo lato server: far compilare tutto per poi
  // scoprire che le password non coincidono è una perdita di tempo inutile.
  const mismatch =
    form.password_confirm.length > 0 && form.password !== form.password_confirm

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (mismatch) return

    setSubmitting(true)
    setError(null)
    try {
      await register(form)
      navigate('/', { replace: true })
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
      navigate('/', { replace: true })
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setGoogleBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-bold text-ink-900">Crea un account</h1>
      <p className="mt-1 text-sm text-ink-500">
        Bastano pochi secondi per iniziare a scrivere sul forum.
      </p>

      <Card className="mt-6 p-6">
        {error && <Alert className="mb-5">{error.message}</Alert>}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Field label="Email" htmlFor="email" error={fieldError('email')}>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              invalid={Boolean(fieldError('email'))}
              onChange={(e) => update('email', e.target.value)}
              placeholder="nome@esempio.it"
            />
          </Field>

          <Field
            label="Nome utente"
            htmlFor="username"
            error={fieldError('username')}
            hint="È il nome che vedranno gli altri utenti sul forum."
          >
            <Input
              id="username"
              autoComplete="username"
              required
              maxLength={50}
              value={form.username}
              invalid={Boolean(fieldError('username'))}
              onChange={(e) => update('username', e.target.value)}
            />
          </Field>

          <Field
            label="Password"
            htmlFor="password"
            error={fieldError('password')}
            hint="Almeno 8 caratteri, non solo numeri."
          >
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={form.password}
              invalid={Boolean(fieldError('password'))}
              onChange={(e) => update('password', e.target.value)}
            />
          </Field>

          <Field
            label="Conferma password"
            htmlFor="password_confirm"
            error={mismatch ? 'Le password non corrispondono.' : undefined}
          >
            <Input
              id="password_confirm"
              type="password"
              autoComplete="new-password"
              required
              value={form.password_confirm}
              invalid={mismatch}
              onChange={(e) => update('password_confirm', e.target.value)}
            />
          </Field>

          <Button
            type="submit"
            loading={submitting}
            disabled={mismatch}
            className="w-full"
          >
            Registrati
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
        Hai già un account?{' '}
        <Link to="/login" className="font-medium text-brand-700 hover:underline">
          Accedi
        </Link>
      </p>
    </div>
  )
}
