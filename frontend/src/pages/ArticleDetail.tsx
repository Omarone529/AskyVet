import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { Alert, Badge, Button, Card, Loading } from '@/components/ui'
import { api, mediaUrl } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { useApi } from '@/lib/hooks'
import { useAuth } from '@/lib/auth'
import type { Article, Thread } from '@/types'

/**
 * Il blog non ha commenti propri: la discussione vive nel forum.
 * Questo riquadro fa da ponte fra i due mondi.
 */
function Discussion({ article }: { article: Article }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const openDiscussion = async () => {
    setCreating(true)
    setError(null)
    try {
      const thread = await api.post<Thread>('/api/forum/threads/', {
        title: article.title,
        content: `Discussione sull'articolo "${article.title}".`,
        article_id: article.id,
      })
      navigate(`/forum/${thread.slug}`)
    } catch (caught) {
      setError((caught as Error).message)
      setCreating(false)
    }
  }

  if (article.discussion) {
    return (
      <Card className="mt-10 p-6">
        <h2 className="text-lg font-semibold text-ink-900">Discussione</h2>
        <p className="mt-1 text-sm text-ink-500">
          {article.discussion.posts_count}{' '}
          {article.discussion.posts_count === 1 ? 'messaggio' : 'messaggi'} sul forum.
        </p>
        <Link to={`/forum/${article.discussion.slug}`} className="mt-4 inline-block">
          <Button variant="secondary">Vai alla discussione</Button>
        </Link>
      </Card>
    )
  }

  return (
    <Card className="mt-10 p-6">
      <h2 className="text-lg font-semibold text-ink-900">Discussione</h2>
      <p className="mt-1 text-sm text-ink-500">
        Non c'è ancora una discussione su questo articolo.
      </p>

      {error && (
        <Alert className="mt-4" tone="error">
          {error}
        </Alert>
      )}

      <div className="mt-4">
        {user ? (
          <Button loading={creating} onClick={openDiscussion}>
            Apri la discussione
          </Button>
        ) : (
          <Link to="/login">
            <Button variant="secondary">Accedi per aprire una discussione</Button>
          </Link>
        )}
      </div>
    </Card>
  )
}

export function ArticleDetail() {
  const { slug } = useParams<{ slug: string }>()

  const { data, loading, error } = useApi(
    () => api.get<Article>(`/api/articles/${slug}/`),
    [slug],
  )

  if (loading) return <Loading />
  if (error) return <Alert>{error}</Alert>
  if (!data) return null

  const cover = mediaUrl(data.cover_image)

  return (
    <article className="mx-auto max-w-3xl">
      <Link to="/" className="text-sm text-brand-700 hover:underline">
        ← Tutti gli articoli
      </Link>

      <header className="mt-4">
        <div className="flex flex-wrap items-center gap-2">
          {data.category && <Badge tone="brand">{data.category.name}</Badge>}
          {data.status === 'draft' && <Badge tone="warning">Bozza</Badge>}
        </div>

        <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight text-ink-900 sm:text-4xl">
          {data.title}
        </h1>

        <p className="mt-3 text-sm text-ink-500">
          {data.author?.username ?? 'Redazione'} ·{' '}
          {formatDate(data.published_at ?? data.created_at)}
        </p>
      </header>

      {cover && (
        <img src={cover} alt="" className="mt-6 w-full rounded-xl object-cover" />
      )}

      {/* Il corpo arriva come testo semplice dal backend: viene reso come tale,
          non con dangerouslySetInnerHTML, per non aprire la porta a XSS. */}
      <div className="article-body mt-8 whitespace-pre-wrap">{data.body}</div>

      {data.tags.length > 0 && (
        <div className="mt-8 flex flex-wrap gap-2 border-t border-slate-200 pt-6">
          {data.tags.map((tag) => (
            <Link key={tag.id} to={`/?tag=${tag.slug}`}>
              <Badge>#{tag.name}</Badge>
            </Link>
          ))}
        </div>
      )}

      <Discussion article={data} />
    </article>
  )
}
