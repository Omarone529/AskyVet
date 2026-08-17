import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  Input,
  Loading,
  Select,
  Textarea,
} from '@/components/ui'
import { ApiError, api, request } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { useApi } from '@/lib/hooks'
import type { ArticleListItem, Category, Paginated, Tag } from '@/types'

interface DraftForm {
  title: string
  body: string
  categoryId: string
  tagIds: number[]
  cover: File | null
  publish: boolean
}

const EMPTY: DraftForm = {
  title: '',
  body: '',
  categoryId: '',
  tagIds: [],
  cover: null,
  publish: false,
}

function ArticleForm({
  categories,
  tags,
  onDone,
  onCancel,
}: {
  categories: Category[]
  tags: Tag[]
  onDone: () => void
  onCancel: () => void
}) {
  const [form, setForm] = useState<DraftForm>(EMPTY)
  const [error, setError] = useState<ApiError | Error | null>(null)
  const [saving, setSaving] = useState(false)

  const fieldError = (name: string) =>
    error instanceof ApiError ? error.fieldError(name) : undefined

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)

    try {
      const body = new FormData()
      body.append('title', form.title)
      body.append('body', form.body)
      body.append('status', form.publish ? 'published' : 'draft')
      if (form.categoryId) body.append('category_id', form.categoryId)
      // Un append per elemento: è così che DRF legge una lista da multipart.
      for (const id of form.tagIds) body.append('tag_ids', String(id))
      if (form.cover) body.append('cover_image', form.cover)

      await request('/api/articles/', { method: 'POST', body })
      onDone()
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="mb-6 p-6">
      <h2 className="mb-4 text-lg font-semibold text-ink-900">Nuovo articolo</h2>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && <Alert>{error.message}</Alert>}

        <Field label="Titolo" htmlFor="title" error={fieldError('title')}>
          <Input
            id="title"
            required
            maxLength={255}
            value={form.title}
            invalid={Boolean(fieldError('title'))}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
        </Field>

        <Field
          label="Contenuto"
          htmlFor="body"
          error={fieldError('body')}
          hint="Gli a capo vengono mantenuti nella pagina pubblica."
        >
          <Textarea
            id="body"
            required
            rows={12}
            value={form.body}
            invalid={Boolean(fieldError('body'))}
            onChange={(e) => setForm({ ...form, body: e.target.value })}
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Categoria" htmlFor="category">
            <Select
              id="category"
              value={form.categoryId}
              onChange={(e) => setForm({ ...form, categoryId: e.target.value })}
            >
              <option value="">Nessuna categoria</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </Select>
          </Field>

          <Field
            label="Immagine di copertina"
            htmlFor="cover"
            error={fieldError('cover_image')}
          >
            <Input
              id="cover"
              type="file"
              accept="image/*"
              onChange={(e) => setForm({ ...form, cover: e.target.files?.[0] ?? null })}
            />
          </Field>
        </div>

        {tags.length > 0 && (
          <fieldset>
            <legend className="mb-2 text-sm font-medium text-ink-900">Tag</legend>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => {
                const checked = form.tagIds.includes(tag.id)
                return (
                  <label
                    key={tag.id}
                    className="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-slate-300 px-3 py-1 text-sm has-checked:border-brand-500 has-checked:bg-brand-50"
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={checked}
                      onChange={() =>
                        setForm({
                          ...form,
                          tagIds: checked
                            ? form.tagIds.filter((id) => id !== tag.id)
                            : [...form.tagIds, tag.id],
                        })
                      }
                    />
                    #{tag.name}
                  </label>
                )
              })}
            </div>
          </fieldset>
        )}

        <label className="flex items-center gap-2 text-sm text-ink-700">
          <input
            type="checkbox"
            checked={form.publish}
            onChange={(e) => setForm({ ...form, publish: e.target.checked })}
          />
          Pubblica subito (altrimenti resta in bozza)
        </label>

        <div className="flex gap-2">
          <Button type="submit" loading={saving}>
            Salva articolo
          </Button>
          <Button variant="ghost" onClick={onCancel}>
            Annulla
          </Button>
        </div>
      </form>
    </Card>
  )
}

function ArticleRow({
  article,
  onChanged,
}: {
  article: ArticleListItem
  onChanged: () => void
}) {
  const [busy, setBusy] = useState(false)
  const published = article.status === 'published'

  const togglePublish = async () => {
    setBusy(true)
    try {
      await api.patch(`/api/articles/${article.slug}/publish/`, {
        published: !published,
      })
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Eliminare "${article.title}"?`)) return
    setBusy(true)
    try {
      await api.delete(`/api/articles/${article.slug}/`)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="flex flex-wrap items-center gap-4 p-4">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={published ? 'success' : 'warning'}>
            {published ? 'Pubblicato' : 'Bozza'}
          </Badge>
          {article.category && <Badge>{article.category.name}</Badge>}
        </div>

        <p className="mt-1 font-medium text-ink-900">
          <Link to={`/articoli/${article.slug}`} className="hover:underline">
            {article.title}
          </Link>
        </p>

        <p className="mt-0.5 text-xs text-ink-500">
          {published
            ? `Pubblicato il ${formatDate(article.published_at)}`
            : `Creato il ${formatDate(article.created_at)}`}
        </p>
      </div>

      <div className="flex gap-2">
        <Button variant="secondary" size="sm" loading={busy} onClick={togglePublish}>
          {published ? 'Riporta in bozza' : 'Pubblica'}
        </Button>
        <Button variant="danger" size="sm" disabled={busy} onClick={handleDelete}>
          Elimina
        </Button>
      </div>
    </Card>
  )
}

export function AdminArticles() {
  const [creating, setCreating] = useState(false)
  const [filter, setFilter] = useState<'all' | 'draft'>('all')

  const categories = useApi(
    () => api.get<Paginated<Category>>('/api/articles/categories/'),
    [],
  )
  const tags = useApi(() => api.get<Paginated<Tag>>('/api/articles/tags/'), [])

  const articles = useApi(
    () =>
      filter === 'draft'
        ? api.get<Paginated<ArticleListItem>>('/api/articles/drafts/')
        : api.get<Paginated<ArticleListItem>>('/api/articles/', { status: 'all' }),
    [filter],
  )

  return (
    <div>
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">Gestione articoli</h1>
          <p className="mt-1 text-sm text-ink-500">
            Crea, pubblica ed elimina i contenuti del blog.
          </p>
        </div>

        {!creating && <Button onClick={() => setCreating(true)}>Nuovo articolo</Button>}
      </header>

      {creating && (
        <ArticleForm
          categories={categories.data?.results ?? []}
          tags={tags.data?.results ?? []}
          onCancel={() => setCreating(false)}
          onDone={() => {
            setCreating(false)
            articles.reload()
          }}
        />
      )}

      <div className="mb-4 flex gap-2">
        <Button
          size="sm"
          variant={filter === 'all' ? 'primary' : 'secondary'}
          onClick={() => setFilter('all')}
        >
          Tutti
        </Button>
        <Button
          size="sm"
          variant={filter === 'draft' ? 'primary' : 'secondary'}
          onClick={() => setFilter('draft')}
        >
          Solo bozze
        </Button>
      </div>

      {articles.loading && <Loading />}
      {articles.error && <Alert>{articles.error}</Alert>}

      {articles.data && articles.data.results.length === 0 && (
        <EmptyState
          title="Nessun articolo"
          description="Crea il primo articolo del blog."
        />
      )}

      <div className="space-y-3">
        {articles.data?.results.map((article) => (
          <ArticleRow key={article.id} article={article} onChanged={articles.reload} />
        ))}
      </div>
    </div>
  )
}
