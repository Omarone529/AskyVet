import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  Alert,
  Avatar,
  Badge,
  Button,
  Card,
  Field,
  Loading,
  Textarea,
  cx,
} from '@/components/ui'
import { api } from '@/lib/api'
import { formatRelative } from '@/lib/format'
import { useApi } from '@/lib/hooks'
import { useAuth } from '@/lib/auth'
import type { Post, Reply, Thread } from '@/types'

/** Cuore del like, con conteggio. */
function LikeButton({
  liked,
  count,
  onToggle,
}: {
  liked: boolean
  count: number
  onToggle: () => Promise<unknown>
}) {
  const { user } = useAuth()
  const [state, setState] = useState({ liked, count })
  const [busy, setBusy] = useState(false)

  const handleClick = async () => {
    // Aggiornamento ottimistico: il cuore reagisce subito, e in caso di errore
    // torna com'era. Aspettare la rete per un like sembra un'app rotta.
    const previous = state
    setState({
      liked: !state.liked,
      count: state.count + (state.liked ? -1 : 1),
    })
    setBusy(true)
    try {
      await onToggle()
    } catch {
      setState(previous)
    } finally {
      setBusy(false)
    }
  }

  if (!user) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs text-ink-400">
        ♡ {state.count}
      </span>
    )
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={busy}
      aria-pressed={state.liked}
      aria-label={state.liked ? 'Togli il like' : 'Metti like'}
      className={cx(
        'inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs transition-colors',
        state.liked ? 'text-red-600 hover:bg-red-50' : 'text-ink-500 hover:bg-slate-100',
      )}
    >
      <span aria-hidden="true">{state.liked ? '♥' : '♡'}</span>
      {state.count}
    </button>
  )
}

/** Form di scrittura, usato sia per creare sia per modificare. */
function MessageForm({
  initialValue = '',
  submitLabel,
  placeholder,
  onSubmit,
  onCancel,
}: {
  initialValue?: string
  submitLabel: string
  placeholder?: string
  onSubmit: (content: string) => Promise<void>
  onCancel?: () => void
}) {
  const [content, setContent] = useState(initialValue)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!content.trim()) return

    setBusy(true)
    setError(null)
    try {
      await onSubmit(content)
      setContent('')
    } catch (caught) {
      setError((caught as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <Alert>{error}</Alert>}
      <Field label="Messaggio">
        <Textarea
          rows={3}
          required
          value={content}
          placeholder={placeholder}
          onChange={(e) => setContent(e.target.value)}
        />
      </Field>
      <div className="flex gap-2">
        <Button type="submit" size="sm" loading={busy}>
          {submitLabel}
        </Button>
        {onCancel && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Annulla
          </Button>
        )}
      </div>
    </form>
  )
}

function ReplyItem({ reply, onChanged }: { reply: Reply; onChanged: () => void }) {
  const { user, isAdmin } = useAuth()
  const [editing, setEditing] = useState(false)

  const canEdit = user?.id === reply.author.id
  const canDelete = canEdit || isAdmin

  const handleDelete = async () => {
    if (!confirm('Eliminare questa risposta?')) return
    await api.delete(`/api/forum/replies/${reply.id}/`)
    onChanged()
  }

  return (
    <div className="flex gap-3 border-l-2 border-slate-100 py-3 pl-4">
      <Avatar username={reply.author.username} src={reply.author.avatar} size={28} />

      <div className="min-w-0 flex-1">
        <p className="text-xs text-ink-500">
          <span className="font-medium text-ink-900">{reply.author.username}</span> ·{' '}
          {formatRelative(reply.created_at)}
        </p>

        {editing ? (
          <div className="mt-2">
            <MessageForm
              initialValue={reply.content}
              submitLabel="Salva"
              onCancel={() => setEditing(false)}
              onSubmit={async (content) => {
                await api.patch(`/api/forum/replies/${reply.id}/`, { content })
                setEditing(false)
                onChanged()
              }}
            />
          </div>
        ) : (
          <>
            <p className="mt-1 whitespace-pre-wrap text-sm text-ink-700">
              {reply.content}
            </p>

            <div className="mt-1 flex items-center gap-1">
              <LikeButton
                liked={reply.is_liked}
                count={reply.likes_count}
                onToggle={() => api.post(`/api/forum/replies/${reply.id}/like/`)}
              />
              {canEdit && (
                <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
                  Modifica
                </Button>
              )}
              {canDelete && (
                <Button variant="ghost" size="sm" onClick={handleDelete}>
                  Elimina
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function PostItem({
  post,
  thread,
  onChanged,
}: {
  post: Post
  thread: Thread
  onChanged: () => void
}) {
  const { user, isAdmin } = useAuth()
  const [replying, setReplying] = useState(false)
  const [editing, setEditing] = useState(false)

  const canEdit = user?.id === post.author.id
  const canDelete = canEdit || isAdmin
  const canPin = isAdmin || user?.id === thread.author.id
  const canWrite = Boolean(user) && !user?.is_muted && !thread.is_closed

  const handleDelete = async () => {
    if (!confirm('Eliminare questo messaggio e le sue risposte?')) return
    await api.delete(`/api/forum/posts/${post.id}/`)
    onChanged()
  }

  return (
    <Card className={cx('p-5', post.is_pinned && 'ring-1 ring-brand-200')}>
      <div className="flex gap-4">
        <Avatar username={post.author.username} src={post.author.avatar} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-ink-900">{post.author.username}</span>
            <span className="text-xs text-ink-500">
              {formatRelative(post.created_at)}
            </span>
            {post.is_pinned && <Badge tone="brand">In evidenza</Badge>}
          </div>

          {editing ? (
            <div className="mt-3">
              <MessageForm
                initialValue={post.content}
                submitLabel="Salva"
                onCancel={() => setEditing(false)}
                onSubmit={async (content) => {
                  await api.patch(`/api/forum/posts/${post.id}/`, { content })
                  setEditing(false)
                  onChanged()
                }}
              />
            </div>
          ) : (
            <>
              <p className="mt-2 whitespace-pre-wrap text-ink-700">{post.content}</p>

              <div className="mt-2 flex flex-wrap items-center gap-1">
                <LikeButton
                  liked={post.is_liked}
                  count={post.likes_count}
                  onToggle={() => api.post(`/api/forum/posts/${post.id}/like/`)}
                />

                {canWrite && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setReplying((v) => !v)}
                  >
                    Rispondi
                  </Button>
                )}
                {canEdit && (
                  <Button variant="ghost" size="sm" onClick={() => setEditing(true)}>
                    Modifica
                  </Button>
                )}
                {canPin && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      await api.post(`/api/forum/posts/${post.id}/pin/`)
                      onChanged()
                    }}
                  >
                    {post.is_pinned ? 'Togli evidenza' : 'Metti in evidenza'}
                  </Button>
                )}
                {canDelete && (
                  <Button variant="ghost" size="sm" onClick={handleDelete}>
                    Elimina
                  </Button>
                )}
              </div>
            </>
          )}

          {post.replies.length > 0 && (
            <div className="mt-3 space-y-1">
              {post.replies.map((reply) => (
                <ReplyItem key={reply.id} reply={reply} onChanged={onChanged} />
              ))}
            </div>
          )}

          {replying && canWrite && (
            <div className="mt-4 border-l-2 border-brand-200 pl-4">
              <MessageForm
                submitLabel="Rispondi"
                placeholder="Scrivi una risposta…"
                onCancel={() => setReplying(false)}
                onSubmit={async (content) => {
                  await api.post(`/api/forum/posts/${post.id}/replies/`, { content })
                  setReplying(false)
                  onChanged()
                }}
              />
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

/** Barra di moderazione, visibile solo ad admin e autore del topic. */
function ModerationBar({
  thread,
  onChanged,
}: {
  thread: Thread
  onChanged: () => void
}) {
  const { user, isAdmin } = useAuth()
  const navigate = useNavigate()

  const isOwner = user?.id === thread.author.id
  if (!isAdmin && !isOwner) return null

  const handleDelete = async () => {
    if (!confirm('Eliminare l’intera discussione?')) return
    await api.delete(`/api/forum/threads/${thread.slug}/`)
    navigate('/forum')
  }

  return (
    <div className="mb-6 flex flex-wrap gap-2">
      {isAdmin && (
        <>
          <Button
            variant="secondary"
            size="sm"
            onClick={async () => {
              await api.patch(`/api/forum/threads/${thread.slug}/pin/`, {
                pinned: !thread.is_pinned,
              })
              onChanged()
            }}
          >
            {thread.is_pinned ? 'Togli dalle evidenze' : 'Metti in evidenza'}
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={async () => {
              await api.patch(`/api/forum/threads/${thread.slug}/close/`, {
                closed: !thread.is_closed,
              })
              onChanged()
            }}
          >
            {thread.is_closed ? 'Riapri discussione' : 'Chiudi discussione'}
          </Button>
        </>
      )}

      <Button variant="danger" size="sm" onClick={handleDelete}>
        Elimina discussione
      </Button>
    </div>
  )
}

export function ThreadDetail() {
  const { slug } = useParams<{ slug: string }>()
  const { user } = useAuth()

  const { data, loading, error, reload } = useApi(
    () => api.get<Thread>(`/api/forum/threads/${slug}/`),
    [slug],
  )

  if (loading) return <Loading />
  if (error) return <Alert>{error}</Alert>
  if (!data) return null

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/forum" className="text-sm text-brand-700 hover:underline">
        ← Tutte le discussioni
      </Link>

      <header className="mt-4 mb-6">
        <div className="flex flex-wrap items-center gap-2">
          {data.is_pinned && <Badge tone="brand">In evidenza</Badge>}
          {data.is_closed && <Badge tone="neutral">Chiuso</Badge>}
          {data.category && <Badge>{data.category.name}</Badge>}
        </div>

        <h1 className="mt-2 text-2xl font-bold tracking-tight text-ink-900 sm:text-3xl">
          {data.title}
        </h1>

        <p className="mt-2 text-sm text-ink-500">
          Aperta da {data.author.username} · {formatRelative(data.created_at)} ·{' '}
          {data.views} visualizzazioni
        </p>

        {data.article && (
          <Card className="mt-4 p-4">
            <p className="text-xs uppercase tracking-wide text-ink-400">
              Discussione sull'articolo
            </p>
            <Link
              to={`/articoli/${data.article.slug}`}
              className="mt-1 block font-medium text-brand-700 hover:underline"
            >
              {data.article.title}
            </Link>
          </Card>
        )}
      </header>

      <ModerationBar thread={data} onChanged={reload} />

      <div className="space-y-4">
        {data.posts.map((post) => (
          <PostItem key={post.id} post={post} thread={data} onChanged={reload} />
        ))}
      </div>

      <div className="mt-8">
        {data.is_closed ? (
          <Alert tone="info">
            Questa discussione è chiusa: non è più possibile scrivere.
          </Alert>
        ) : !user ? (
          <Card className="flex items-center justify-between gap-4 p-4">
            <p className="text-sm text-ink-500">Accedi per partecipare.</p>
            <Link to="/login">
              <Button size="sm">Accedi</Button>
            </Link>
          </Card>
        ) : user.is_muted ? (
          <Alert tone="warning">
            Sei temporaneamente silenziato e non puoi scrivere.
          </Alert>
        ) : (
          <Card className="p-5">
            <h2 className="mb-3 font-semibold text-ink-900">Scrivi un messaggio</h2>
            <MessageForm
              submitLabel="Pubblica"
              placeholder="Il tuo contributo…"
              onSubmit={async (content) => {
                await api.post(`/api/forum/threads/${data.slug}/posts/`, { content })
                reload()
              }}
            />
          </Card>
        )}
      </div>
    </div>
  )
}
