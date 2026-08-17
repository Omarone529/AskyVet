import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

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
  Textarea,
} from '@/components/ui'
import { api } from '@/lib/api'
import { formatRelative } from '@/lib/format'
import { useApi, useDebounced } from '@/lib/hooks'
import { useAuth } from '@/lib/auth'
import type { ForumCategory, Paginated, Thread, ThreadListItem } from '@/types'

function ThreadRow({ thread }: { thread: ThreadListItem }) {
  return (
    <Card className="p-4 transition-shadow hover:shadow-md">
      <div className="flex gap-4">
        <Avatar username={thread.author.username} src={thread.author.avatar} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            {thread.is_pinned && <Badge tone="brand">In evidenza</Badge>}
            {thread.is_closed && <Badge tone="neutral">Chiuso</Badge>}
            {thread.category && <Badge>{thread.category.name}</Badge>}
          </div>

          <h2 className="mt-1 font-semibold text-ink-900">
            <Link to={`/forum/${thread.slug}`} className="hover:underline">
              {thread.title}
            </Link>
          </h2>

          {thread.article && (
            <p className="mt-1 text-xs text-ink-500">
              Discussione sull'articolo{' '}
              <Link
                to={`/articoli/${thread.article.slug}`}
                className="text-brand-700 hover:underline"
              >
                {thread.article.title}
              </Link>
            </p>
          )}

          <p className="mt-2 text-xs text-ink-500">
            {thread.author.username} · {formatRelative(thread.created_at)} ·{' '}
            {thread.posts_count} {thread.posts_count === 1 ? 'messaggio' : 'messaggi'}{' '}
            · {thread.views} visualizzazioni
          </p>

          {thread.last_post && (
            <p className="mt-1 text-xs text-ink-400">
              Ultimo messaggio di {thread.last_post.author}{' '}
              {formatRelative(thread.last_post.created_at)}
            </p>
          )}
        </div>
      </div>
    </Card>
  )
}

function NewThreadForm({
  categories,
  onCreated,
}: {
  categories: ForumCategory[]
  onCreated: (slug: string) => void
}) {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const thread = await api.post<Thread>('/api/forum/threads/', {
        title,
        content,
        category_id: categoryId ? Number(categoryId) : null,
      })
      onCreated(thread.slug)
    } catch (caught) {
      setError((caught as Error).message)
      setSubmitting(false)
    }
  }

  if (!user) {
    return (
      <Card className="mb-6 flex items-center justify-between gap-4 p-4">
        <p className="text-sm text-ink-500">Accedi per aprire una nuova discussione.</p>
        <Link to="/login">
          <Button size="sm">Accedi</Button>
        </Link>
      </Card>
    )
  }

  // Il backend rifiuterebbe comunque con 403: dirlo prima evita di far
  // scrivere un messaggio che verrebbe buttato via.
  if (user.is_muted) {
    return (
      <Alert tone="warning" className="mb-6">
        Sei temporaneamente silenziato e non puoi aprire nuove discussioni.
      </Alert>
    )
  }

  if (!open) {
    return (
      <div className="mb-6">
        <Button onClick={() => setOpen(true)}>Apri una discussione</Button>
      </div>
    )
  }

  return (
    <Card className="mb-6 p-5">
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && <Alert>{error}</Alert>}

        <Field label="Titolo" htmlFor="title">
          <Input
            id="title"
            required
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Di cosa vuoi parlare?"
          />
        </Field>

        <Field label="Messaggio" htmlFor="content">
          <Textarea
            id="content"
            required
            rows={5}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Scrivi il primo messaggio della discussione…"
          />
        </Field>

        <Field label="Categoria" htmlFor="category">
          <Select
            id="category"
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
          >
            <option value="">Nessuna categoria</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </Field>

        <div className="flex gap-2">
          <Button type="submit" loading={submitting}>
            Pubblica
          </Button>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Annulla
          </Button>
        </div>
      </form>
    </Card>
  )
}

export function Threads() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()

  const page = Number(params.get('page') ?? 1)
  const category = params.get('category') ?? ''

  const [searchInput, setSearchInput] = useState(params.get('search') ?? '')
  const search = useDebounced(searchInput)

  const categories = useApi(
    () => api.get<Paginated<ForumCategory>>('/api/forum/categories/'),
    [],
  )

  const threads = useApi(
    () =>
      api.get<Paginated<ThreadListItem>>('/api/forum/threads/', {
        page,
        category,
        search,
      }),
    [page, category, search],
  )

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next)
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-ink-900">Forum</h1>
        <p className="mt-2 text-ink-500">
          Domande, esperienze e discussioni della community.
        </p>
      </header>

      <NewThreadForm
        categories={categories.data?.results ?? []}
        onCreated={(slug) => navigate(`/forum/${slug}`)}
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <Input
          type="search"
          placeholder="Cerca fra le discussioni…"
          aria-label="Cerca fra le discussioni"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value)
            setParam('search', e.target.value)
          }}
          className="sm:flex-1"
        />

        <Select
          aria-label="Filtra per categoria"
          value={category}
          onChange={(e) => setParam('category', e.target.value)}
          className="sm:w-56"
        >
          <option value="">Tutte le categorie</option>
          {categories.data?.results.map((item) => (
            <option key={item.id} value={item.slug}>
              {item.name}
            </option>
          ))}
        </Select>
      </div>

      {threads.loading && <Loading />}
      {threads.error && <Alert>{threads.error}</Alert>}

      {threads.data && threads.data.results.length === 0 && (
        <EmptyState
          title="Nessuna discussione"
          description={
            search || category
              ? 'Prova a modificare la ricerca o a rimuovere i filtri.'
              : 'Sii il primo ad aprirne una.'
          }
        />
      )}

      {threads.data && threads.data.results.length > 0 && (
        <>
          <div className="space-y-3">
            {threads.data.results.map((thread) => (
              <ThreadRow key={thread.id} thread={thread} />
            ))}
          </div>

          <Pagination
            page={page}
            count={threads.data.count}
            onChange={(next) => setParam('page', String(next))}
          />
        </>
      )}
    </div>
  )
}
