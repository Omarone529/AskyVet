import { useState, type FormEvent } from 'react'

import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  Input,
  Loading,
  Pagination,
  Select,
} from '@/components/ui'
import { ApiError, api } from '@/lib/api'
import { formatDate, formatDateTime } from '@/lib/format'
import { useApi, useDebounced } from '@/lib/hooks'
import { useAuth } from '@/lib/auth'
import type { AdminUser, Paginated } from '@/types'

/** Durate offerte per il mute. 0 revoca la limitazione. */
const MUTE_OPTIONS = [
  { hours: 1, label: '1 ora' },
  { hours: 24, label: '1 giorno' },
  { hours: 24 * 7, label: '1 settimana' },
  { hours: 24 * 30, label: '1 mese' },
]

function NewAdminForm({ onDone }: { onDone: () => void }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [saving, setSaving] = useState(false)

  const fieldError = (name: string) =>
    error instanceof ApiError ? error.fieldError(name) : undefined

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await api.post('/api/users/admins/', form)
      setForm({ email: '', username: '', password: '', password_confirm: '' })
      setOpen(false)
      onDone()
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return <Button onClick={() => setOpen(true)}>Nuovo amministratore</Button>
  }

  return (
    <Card className="w-full p-6">
      <h2 className="mb-4 text-lg font-semibold text-ink-900">Nuovo amministratore</h2>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && <Alert>{error.message}</Alert>}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Email" htmlFor="admin-email" error={fieldError('email')}>
            <Input
              id="admin-email"
              type="email"
              required
              value={form.email}
              invalid={Boolean(fieldError('email'))}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </Field>

          <Field
            label="Nome utente"
            htmlFor="admin-username"
            error={fieldError('username')}
          >
            <Input
              id="admin-username"
              required
              value={form.username}
              invalid={Boolean(fieldError('username'))}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </Field>

          <Field
            label="Password"
            htmlFor="admin-password"
            error={fieldError('password')}
          >
            <Input
              id="admin-password"
              type="password"
              required
              value={form.password}
              invalid={Boolean(fieldError('password'))}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </Field>

          <Field label="Conferma password" htmlFor="admin-confirm">
            <Input
              id="admin-confirm"
              type="password"
              required
              value={form.password_confirm}
              onChange={(e) => setForm({ ...form, password_confirm: e.target.value })}
            />
          </Field>
        </div>

        <div className="flex gap-2">
          <Button type="submit" loading={saving}>
            Crea amministratore
          </Button>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Annulla
          </Button>
        </div>
      </form>
    </Card>
  )
}

function UserRow({ user, onChanged }: { user: AdminUser; onChanged: () => void }) {
  const { user: me } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Il backend rifiuta questi casi con 403: nasconderli evita di offrire
  // un'azione che fallirebbe comunque.
  const isSelf = user.id === me?.id
  const untouchable = isSelf || user.is_admin

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true)
    setError(null)
    try {
      await action()
      onChanged()
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const ban = () => {
    const reason = prompt('Motivo del ban:')
    if (!reason) return
    return run(() => api.patch(`/api/users/${user.id}/ban/`, { banned: true, reason }))
  }

  const unban = () =>
    run(() => api.patch(`/api/users/${user.id}/ban/`, { banned: false }))

  const mute = (hours: number) => {
    if (hours === 0) {
      return run(() => api.patch(`/api/users/${user.id}/mute/`, { hours: 0 }))
    }
    const reason = prompt('Motivo della limitazione:')
    if (!reason) return
    return run(() => api.patch(`/api/users/${user.id}/mute/`, { hours, reason }))
  }

  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center gap-4">
        <Avatar username={user.username} src={user.avatar} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-ink-900">{user.username}</span>
            {user.is_admin && <Badge tone="brand">Admin</Badge>}
            {!user.is_active && <Badge tone="danger">Bannato</Badge>}
            {user.is_muted && <Badge tone="warning">Silenziato</Badge>}
            {isSelf && <Badge>Tu</Badge>}
          </div>

          <p className="mt-0.5 text-sm text-ink-500">{user.email}</p>
          <p className="mt-0.5 text-xs text-ink-400">
            Iscritto il {formatDate(user.created_at)}
            {user.is_muted &&
              ` · silenziato fino al ${formatDateTime(user.muted_until)}`}
          </p>

          {user.moderation_reason && (
            <p className="mt-1 text-xs text-ink-500">
              Motivo: {user.moderation_reason}
            </p>
          )}
        </div>

        {!untouchable && (
          <div className="flex flex-wrap items-center gap-2">
            {user.is_muted ? (
              <Button
                variant="secondary"
                size="sm"
                disabled={busy}
                onClick={() => mute(0)}
              >
                Togli limitazione
              </Button>
            ) : (
              <Select
                aria-label={`Silenzia ${user.username}`}
                value=""
                disabled={busy}
                className="w-40"
                onChange={(e) => e.target.value && mute(Number(e.target.value))}
              >
                <option value="">Silenzia per…</option>
                {MUTE_OPTIONS.map((option) => (
                  <option key={option.hours} value={option.hours}>
                    {option.label}
                  </option>
                ))}
              </Select>
            )}

            {user.is_active ? (
              <Button variant="danger" size="sm" disabled={busy} onClick={ban}>
                Banna
              </Button>
            ) : (
              <Button variant="secondary" size="sm" disabled={busy} onClick={unban}>
                Riattiva
              </Button>
            )}
          </div>
        )}
      </div>

      {error && (
        <Alert className="mt-3" tone="error">
          {error}
        </Alert>
      )}
    </Card>
  )
}

export function AdminUsers() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const search = useDebounced(searchInput)

  const users = useApi(
    () => api.get<Paginated<AdminUser>>('/api/users/', { page, status, search }),
    [page, status, search],
  )

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">Gestione utenti</h1>
          <p className="mt-1 text-sm text-ink-500">
            Nomina amministratori, banna o limita gli utenti.
          </p>
        </div>

        <NewAdminForm onDone={users.reload} />
      </header>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <Input
          type="search"
          placeholder="Cerca per nome utente…"
          aria-label="Cerca per nome utente"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value)
            setPage(1)
          }}
          className="sm:flex-1"
        />

        <Select
          aria-label="Filtra per stato"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value)
            setPage(1)
          }}
          className="sm:w-48"
        >
          <option value="">Tutti</option>
          <option value="active">Attivi</option>
          <option value="banned">Bannati</option>
          <option value="admin">Amministratori</option>
        </Select>
      </div>

      {users.loading && <Loading />}
      {users.error && <Alert>{users.error}</Alert>}

      {users.data && users.data.results.length === 0 && (
        <EmptyState title="Nessun utente trovato" />
      )}

      <div className="space-y-3">
        {users.data?.results.map((user) => (
          <UserRow key={user.id} user={user} onChanged={users.reload} />
        ))}
      </div>

      {users.data && (
        <Pagination page={page} count={users.data.count} onChange={setPage} />
      )}
    </div>
  )
}
