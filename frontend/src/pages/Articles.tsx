import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import {
  Alert,
  Badge,
  Card,
  EmptyState,
  Input,
  Loading,
  Pagination,
  Select,
  Skeleton,
} from '@/components/ui'
import { api, mediaUrl } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { useApi, useDebounced } from '@/lib/hooks'
import type { ArticleListItem, Category, Paginated } from '@/types'

function ArticleCard({ article }: { article: ArticleListItem }) {
  const cover = mediaUrl(article.cover_image)

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <Link to={`/articoli/${article.slug}`} className="block">
        {cover ? (
          <img src={cover} alt="" className="h-44 w-full object-cover" loading="lazy" />
        ) : (
          <div className="flex h-44 w-full items-center justify-center bg-brand-50 text-4xl">
            🐾
          </div>
        )}

        <div className="p-5">
          {article.category && <Badge tone="brand">{article.category.name}</Badge>}

          <h2 className="mt-2 text-lg font-semibold leading-snug text-ink-900">
            {article.title}
          </h2>

          <p className="mt-3 text-xs text-ink-500">
            {article.author?.username ?? 'Redazione'} ·{' '}
            {formatDate(article.published_at ?? article.created_at)}
          </p>

          {article.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {article.tags.slice(0, 3).map((tag) => (
                <Badge key={tag.id}>#{tag.name}</Badge>
              ))}
            </div>
          )}
        </div>
      </Link>
    </Card>
  )
}

/**
 * La sagoma di ArticleCard: stesse proporzioni, così quando arrivano i dati la
 * pagina non sobbalza.
 */
function ArticleCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <Skeleton className="h-44 w-full rounded-none" />

      <div className="p-5">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="mt-2 h-5 w-full" />
        <Skeleton className="mt-1.5 h-5 w-2/3" />
        <Skeleton className="mt-4 h-3 w-40" />
      </div>
    </Card>
  )
}

/**
 * Occupa la griglia mentre gli articoli arrivano.
 *
 * Sei sagome: riempiono le tre colonne del desktop senza promettere quanti
 * articoli ci saranno davvero.
 */
function ArticlesSkeleton() {
  return (
    <div
      className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
      role="status"
      aria-busy="true"
    >
      {/* Muto per gli occhi, non per gli screen reader: la sagoma da sola non
          direbbe nulla a chi non la vede. */}
      <span className="sr-only">Caricamento degli articoli…</span>

      {Array.from({ length: 6 }, (_, i) => (
        <ArticleCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function Articles() {
  // I filtri vivono nell'URL: una ricerca resta valida se si ricarica o si
  // condivide il link, e il tasto "indietro" si comporta come ci si aspetta.
  const [params, setParams] = useSearchParams()

  const page = Number(params.get('page') ?? 1)
  const category = params.get('category') ?? ''

  const [searchInput, setSearchInput] = useState(params.get('search') ?? '')
  const search = useDebounced(searchInput)

  const categories = useApi(
    () => api.get<Paginated<Category>>('/api/articles/categories/'),
    [],
  )

  const articles = useApi(
    () =>
      api.get<Paginated<ArticleListItem>>('/api/articles/', {
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
    // Cambiando filtro si torna alla prima pagina: restare su pagina 4 con
    // meno risultati mostrerebbe una schermata vuota.
    if (key !== 'page') next.delete('page')
    setParams(next)
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-ink-900">Articoli</h1>
        <p className="mt-2 text-ink-500">
          Divulgazione veterinaria a cura della redazione.
        </p>
      </header>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <Input
          type="search"
          placeholder="Cerca fra gli articoli…"
          aria-label="Cerca fra gli articoli"
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

      {/* Prima apertura (è qui che si paga l'eventuale risveglio del backend):
          la griglia di sagome. Sui ricaricamenti successivi i risultati
          precedenti restano a schermo, quindi basta lo spinner. */}
      {articles.loading && !articles.data && <ArticlesSkeleton />}
      {articles.loading && articles.data && <Loading />}
      {articles.error && <Alert>{articles.error}</Alert>}

      {articles.data && articles.data.results.length === 0 && (
        <EmptyState
          title="Nessun articolo trovato"
          description={
            search || category
              ? 'Prova a modificare la ricerca o a rimuovere i filtri.'
              : 'Non è ancora stato pubblicato nulla.'
          }
        />
      )}

      {articles.data && articles.data.results.length > 0 && (
        <>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {articles.data.results.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>

          <Pagination
            page={page}
            count={articles.data.count}
            onChange={(next) => setParam('page', String(next))}
          />
        </>
      )}
    </div>
  )
}
