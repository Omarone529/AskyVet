import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Button, EmptyState } from '@/components/ui'
import { AdminArticles } from '@/pages/AdminArticles'
import { AdminUsers } from '@/pages/AdminUsers'
import { ArticleDetail } from '@/pages/ArticleDetail'
import { Articles } from '@/pages/Articles'
import { AuthProvider } from '@/lib/auth'
import { Login } from '@/pages/Login'
import { Profile } from '@/pages/Profile'
import { Register } from '@/pages/Register'
import { ThreadDetail } from '@/pages/ThreadDetail'
import { Threads } from '@/pages/Threads'

import './index.css'

function NotFound() {
  return (
    <EmptyState
      title="Pagina non trovata"
      description="Il link potrebbe essere sbagliato o il contenuto è stato rimosso."
      action={
        <Link to="/">
          <Button>Torna agli articoli</Button>
        </Link>
      }
    />
  )
}

const root = document.getElementById('root')
if (!root) throw new Error('Elemento #root non trovato in index.html.')

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      {/* AuthProvider dentro il router: il logout naviga, e useNavigate
          funziona solo sotto un router. */}
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            {/* Pubbliche */}
            <Route index element={<Articles />} />
            <Route path="articoli/:slug" element={<ArticleDetail />} />
            <Route path="forum" element={<Threads />} />
            <Route path="forum/:slug" element={<ThreadDetail />} />
            <Route path="login" element={<Login />} />
            <Route path="registrati" element={<Register />} />

            {/* Richiedono l'accesso */}
            <Route element={<ProtectedRoute />}>
              <Route path="profilo" element={<Profile />} />
            </Route>

            {/* Riservate agli amministratori */}
            <Route element={<ProtectedRoute adminOnly />}>
              <Route path="admin/articoli" element={<AdminArticles />} />
              <Route path="admin/utenti" element={<AdminUsers />} />
            </Route>

            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
