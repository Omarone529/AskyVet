import { useState, type FormEvent } from 'react'

import { Alert, Avatar, Badge, Button, Card, Field, Input } from '@/components/ui'
import { ApiError, request } from '@/lib/api'
import { formatDate, formatDateTime } from '@/lib/format'
import { useAuth } from '@/lib/auth'

export function Profile() {
  const { user, refreshUser } = useAuth()

  const [username, setUsername] = useState(user?.username ?? '')
  const [avatar, setAvatar] = useState<File | null>(null)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  if (!user) return null

  const fieldError = (name: string) =>
    error instanceof ApiError ? error.fieldError(name) : undefined

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    setSaved(false)

    try {
      // FormData e non JSON: è l'unico modo di allegare il file dell'avatar.
      // Il campo va incluso solo se l'utente ne ha scelto uno nuovo, altrimenti
      // una stringa vuota cancellerebbe l'immagine esistente.
      const body = new FormData()
      body.append('username', username)
      if (avatar) body.append('avatar', avatar)

      await request('/api/users/me/', { method: 'PATCH', body })
      await refreshUser()
      setAvatar(null)
      setSaved(true)
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-ink-900">Il mio profilo</h1>

      <Card className="mt-6 p-6">
        <div className="flex items-center gap-4 border-b border-slate-100 pb-5">
          <Avatar username={user.username} src={user.avatar} size={64} />
          <div>
            <p className="font-semibold text-ink-900">{user.username}</p>
            <p className="text-sm text-ink-500">{user.email}</p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {user.is_admin && <Badge tone="brand">Amministratore</Badge>}
              {user.is_muted && <Badge tone="warning">Silenziato</Badge>}
            </div>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-4 border-b border-slate-100 py-5 text-sm">
          <div>
            <dt className="text-ink-500">Iscritto dal</dt>
            <dd className="mt-0.5 font-medium text-ink-900">
              {formatDate(user.created_at)}
            </dd>
          </div>
          {user.is_muted && (
            <div>
              <dt className="text-ink-500">Silenziato fino al</dt>
              <dd className="mt-0.5 font-medium text-amber-700">
                {formatDateTime(user.muted_until)}
              </dd>
            </div>
          )}
        </dl>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4" noValidate>
          {error && <Alert>{error.message}</Alert>}
          {saved && <Alert tone="success">Profilo aggiornato.</Alert>}

          <Field label="Nome utente" htmlFor="username" error={fieldError('username')}>
            <Input
              id="username"
              required
              maxLength={50}
              value={username}
              invalid={Boolean(fieldError('username'))}
              onChange={(e) => setUsername(e.target.value)}
            />
          </Field>

          <Field
            label="Avatar"
            htmlFor="avatar"
            error={fieldError('avatar')}
            hint="Immagine quadrata, formato JPG o PNG."
          >
            <Input
              id="avatar"
              type="file"
              accept="image/*"
              onChange={(e) => setAvatar(e.target.files?.[0] ?? null)}
            />
          </Field>

          <Button type="submit" loading={saving}>
            Salva modifiche
          </Button>
        </form>
      </Card>
    </div>
  )
}
