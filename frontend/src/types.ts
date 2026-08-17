/**
 * Forma dei dati restituiti dall'API.
 *
 * Rispecchia i serializer del backend. Se un campo cambia lì, va cambiato qui:
 * è il punto in cui un disallineamento con il backend viene intercettato in
 * fase di build invece che a pagina aperta.
 */

/** Risposta paginata standard (config/pagination.py, PageNumberPagination). */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// ------------------------------------------------------------------- Utenti

/** users.serializers.UserSerializer — dati pubblici di un utente. */
export interface PublicUser {
  id: string
  username: string
  avatar: string | null
  created_at: string
}

/** users.serializers.UserDetailSerializer — profilo dell'utente loggato. */
export interface CurrentUser {
  id: string
  email: string
  username: string
  avatar: string | null
  is_admin: boolean
  is_muted: boolean
  muted_until: string | null
  created_at: string
  updated_at: string
}

/** users.serializers.AdminUserSerializer — vista del pannello di moderazione. */
export interface AdminUser {
  id: string
  email: string
  username: string
  avatar: string | null
  is_admin: boolean
  is_active: boolean
  is_muted: boolean
  muted_until: string | null
  moderation_reason: string
  created_at: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

/** Risposta di POST /api/auth/login/. */
export interface LoginResponse extends AuthTokens {
  user: CurrentUser
}

// ----------------------------------------------------------------- Articoli

export type ArticleStatus = 'draft' | 'published'

export interface Category {
  id: number
  name: string
  slug: string
  description: string | null
}

export interface Tag {
  id: number
  name: string
  slug: string
}

/** articles.serializers.ArticleListSerializer — senza il corpo. */
export interface ArticleListItem {
  id: string
  author: PublicUser | null
  title: string
  slug: string
  cover_image: string | null
  category: Category | null
  tags: Tag[]
  status: ArticleStatus
  published_at: string | null
  created_at: string
}

/** Topic del forum collegato a un articolo, se esiste. */
export interface ArticleDiscussion {
  id: number
  slug: string
  title: string
  posts_count: number
}

/** articles.serializers.ArticleDetailSerializer — con corpo e discussione. */
export interface Article extends ArticleListItem {
  body: string
  discussion: ArticleDiscussion | null
  updated_at: string
}

// -------------------------------------------------------------------- Forum

export interface ForumCategory {
  id: number
  name: string
  slug: string
  description: string
  order: number
}

/** Articolo citato da un topic, in forma ridotta. */
export interface ThreadArticle {
  id: string
  title: string
  slug: string
  cover_image: string | null
}

export interface Reply {
  id: number
  post: number
  author: PublicUser
  content: string
  likes_count: number
  is_liked: boolean
  created_at: string
  updated_at: string
}

export interface Post {
  id: number
  thread: number
  author: PublicUser
  content: string
  likes_count: number
  is_liked: boolean
  is_pinned: boolean
  replies: Reply[]
  created_at: string
  updated_at: string
}

export interface ThreadLastPost {
  author: string | null
  created_at: string
}

/** forum.serializers.ThreadListSerializer. */
export interface ThreadListItem {
  id: number
  title: string
  slug: string
  author: PublicUser
  category: ForumCategory | null
  article: ThreadArticle | null
  posts_count: number
  last_post: ThreadLastPost | null
  is_pinned: boolean
  is_closed: boolean
  views: number
  created_at: string
  updated_at: string
}

/** forum.serializers.ThreadDetailSerializer. */
export interface Thread extends Omit<ThreadListItem, 'last_post'> {
  posts: Post[]
  pinned_posts: Post[]
}
